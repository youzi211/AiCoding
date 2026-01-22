"""
图片提取模块

从 PDF、DOCX 等文档中提取图片，并支持通过视觉模型生成图片描述。
"""
import base64
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Callable, Optional


class ImageDescriptionCache:
    """图片描述缓存管理器"""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录，默认为 image_descriptions
        """
        if cache_dir is None:
            cache_dir = Path("image_descriptions")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "descriptions.json"
        self._cache_data: dict[str, str] = {}
        self._load()

    def _get_image_hash(self, image_bytes: bytes) -> str:
        """计算图片内容的哈希值作为缓存键"""
        return hashlib.sha256(image_bytes).hexdigest()

    def _load(self) -> None:
        """从文件加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache_data = {}
        else:
            self._cache_data = {}

    def _save(self) -> None:
        """保存缓存到文件"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"缓存保存失败: {e}")

    def get(self, image_bytes: bytes) -> Optional[str]:
        """
        获取图片的缓存描述

        Args:
            image_bytes: 图片二进制数据

        Returns:
            缓存的描述，如果不存在则返回 None
        """
        image_hash = self._get_image_hash(image_bytes)
        return self._cache_data.get(image_hash)

    def set(self, image_bytes: bytes, description: str) -> None:
        """
        设置图片描述缓存

        Args:
            image_bytes: 图片二进制数据
            description: 图片描述
        """
        image_hash = self._get_image_hash(image_bytes)
        self._cache_data[image_hash] = description
        self._save()

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache_data.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()

    def get_cache_stats(self) -> dict[str, int]:
        """获取缓存统计信息"""
        return {
            "total_cached": len(self._cache_data),
            "cache_file_size": self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }


class ImageInfo:
    """图片信息类"""

    __slots__ = ["image_data", "page", "index", "format", "position_hint", "description"]

    def __init__(
        self,
        image_data: bytes,
        page: Optional[int] = None,
        index: int = 0,
        format: str = "png",
        position_hint: Optional[str] = None,
    ):
        """
        Args:
            image_data: 图片二进制数据
            page: 所在页码（PDF）
            index: 图片索引
            format: 图片格式 (png, jpg, etc.)
            position_hint: 位置提示（用于推断在文档中的位置）
        """
        self.image_data = image_data
        self.page = page
        self.index = index
        self.format = format
        self.position_hint = position_hint
        self.description: Optional[str] = None

    def to_base64(self) -> str:
        """转换为 base64 编码"""
        return base64.b64encode(self.image_data).decode("utf-8")

    def save(self, output_dir: Path, prefix: str = "img") -> Path:
        """保存图片到磁盘"""
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{prefix}_{self.page or 'doc'}_{self.index + 1}.{self.format}"
        filepath = output_dir / filename

        with open(filepath, "wb") as f:
            f.write(self.image_data)

        return filepath


class PDFImageExtractor:
    """PDF 图片提取器 - 保持图片位置信息"""

    def extract(self, file_path: Path) -> list[ImageInfo]:
        """
        从 PDF 中提取图片，保留页码和位置信息

        Args:
            file_path: PDF 文件路径

        Returns:
            按页码排序的图片列表
        """
        images = []

        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PDF 图片提取需要安装 PyMuPDF 库。\n"
                "请运行: pip install pymupdf"
            )

        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)

                if base_image:
                    image_bytes = base_image["image"]
                    image_format = base_image.get("ext", "png")

                    # 获取图片在页面中的位置信息
                    try:
                        rect = page.get_image_rects(xref)
                        if rect:
                            position_hint = f"{page_num}_{rect[0].y}_{rect[0].x}"
                        else:
                            position_hint = f"{page_num}_{img_index}"
                    except Exception:
                        position_hint = f"{page_num}_{img_index}"

                    info = ImageInfo(
                        image_data=image_bytes,
                        page=page_num + 1,
                        index=img_index,
                        format=image_format,
                        position_hint=position_hint,
                    )
                    images.append(info)

        doc.close()

        # 按页码和位置排序
        images.sort(key=lambda x: (x.page or 0, x.position_hint or ""))

        return images


class DocxImageExtractor:
    """DOCX 图片提取器 - 保持图片位置信息"""

    def extract(self, file_path: Path) -> list[ImageInfo]:
        """
        从 DOCX 中提取图片，按在文档中出现的顺序排列

        Args:
            file_path: DOCX 文件路径

        Returns:
            按文档顺序排列的图片列表
        """
        images = []

        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "DOCX 图片提取需要安装 python-docx 库。\n"
                "请运行: pip install python-docx"
            )

        doc = Document(file_path)
        image_index = 0

        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_data = rel.target_part.blob
                content_type = rel.target_part.content_type

                format_map = {
                    "image/png": "png",
                    "image/jpeg": "jpg",
                    "image/jpg": "jpg",
                    "image/gif": "gif",
                    "image/bmp": "bmp",
                    "image/svg+xml": "svg",
                }
                image_format = format_map.get(content_type, "png")

                info = ImageInfo(
                    image_data=image_data,
                    page=None,
                    index=image_index,
                    format=image_format,
                    position_hint=f"docx_{image_index}",
                )
                images.append(info)
                image_index += 1

        return images


class ImageExtractor:
    """统一的图片提取器"""

    def __init__(self, use_cache: bool = True, cache_dir: Optional[Path] = None):
        """
        初始化图片提取器

        Args:
            use_cache: 是否使用缓存
            cache_dir: 缓存目录路径
        """
        self.pdf_extractor = PDFImageExtractor()
        self.docx_extractor = DocxImageExtractor()
        self.use_cache = use_cache
        self.cache = ImageDescriptionCache(cache_dir) if use_cache else None

    def extract_from_file(self, file_path: Path) -> list[ImageInfo]:
        """
        根据文件类型提取图片

        Args:
            file_path: 文件路径

        Returns:
            提取的图片列表
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self.pdf_extractor.extract(file_path)
        elif suffix in [".docx", ".doc"]:
            return self.docx_extractor.extract(file_path)
        else:
            return []

    def generate_descriptions(
        self,
        images: list[ImageInfo],
        describe_func: Callable[[bytes], str],
        show_progress: bool = False,
    ) -> None:
        """
        为图片列表批量生成描述（支持缓存）

        Args:
            images: 图片信息列表
            describe_func: 图片描述函数，接收图片二进制数据，返回描述文本
            show_progress: 是否显示进度
        """
        total = len(images)
        cache_hits = 0
        cache_misses = 0

        for i, img in enumerate(images):
            if show_progress:
                print(f"正在生成图片描述 {i + 1}/{total}...")

            try:
                # 尝试从缓存获取
                cached_description = None
                if self.cache:
                    cached_description = self.cache.get(img.image_data)

                if cached_description is not None:
                    # 缓存命中
                    img.description = cached_description
                    cache_hits += 1
                    if show_progress:
                        print(f"  ✓ 使用缓存")
                else:
                    # 缓存未命中，调用模型生成
                    description = describe_func(img.image_data)
                    img.description = description
                    cache_misses += 1

                    # 保存到缓存
                    if self.cache:
                        self.cache.set(img.image_data, description)
            except Exception as e:
                print(f"图片 {img.index} 描述生成失败: {e}")
                img.description = "[图片描述生成失败]"

        # 打印缓存统计
        if show_progress and self.cache:
            stats = self.cache.get_cache_stats()
            print(f"\n缓存统计: 命中 {cache_hits} 次，未命中 {cache_misses} 次")
            print(f"缓存总数: {stats['total_cached']} 个图片")


class TextWithImagesRebuilder:
    """将图片描述插入到原文档相应位置的重建器"""

    PLACEHOLDER_FORMAT = "\n\n[图片描述: {description}]\n\n"

    @staticmethod
    def rebuild_for_pdf(text: str, images: list[ImageInfo]) -> str:
        """
        将图片描述插入到 PDF 文本的相应位置

        策略：在每页文本后插入该页的图片描述

        Args:
            text: 原始文本（按 \n\n 分页）
            images: 图片信息列表

        Returns:
            插入图片描述后的文本
        """
        if not images:
            return text

        # 按页码分组图片
        page_images: dict[int, list[ImageInfo]] = defaultdict(list)
        for img in images:
            if img.page is not None:
                page_images[img.page].append(img)

        # 将文本按页分割
        pages = text.split("\n\n")
        result_pages = []

        for i, page_text in enumerate(pages):
            page_num = i + 1
            result_pages.append(page_text)

            if page_num in page_images:
                for img in page_images[page_num]:
                    if img.description:
                        result_pages.append(
                            TextWithImagesRebuilder.PLACEHOLDER_FORMAT.format(
                                description=img.description
                            )
                        )

        return "\n\n".join(result_pages)

    @staticmethod
    def rebuild_for_docx(text: str, images: list[ImageInfo]) -> str:
        """
        将图片描述插入到 DOCX 文本的相应位置

        策略：在空行处插入图片描述

        Args:
            text: 原始文本
            images: 图片信息列表

        Returns:
            插入图片描述后的文本
        """
        if not images:
            return text

        lines = text.split("\n")
        result = []
        image_index = 0

        for line in lines:
            result.append(line)

            if line.strip() == "" and image_index < len(images):
                img = images[image_index]
                if img.description:
                    result.append(
                        TextWithImagesRebuilder.PLACEHOLDER_FORMAT.format(
                            description=img.description
                        )
                    )
                    image_index += 1

        return "\n".join(result)

    @classmethod
    def rebuild(cls, file_path: Path, text: str, images: list[ImageInfo]) -> str:
        """
        根据文件类型选择合适的重建策略

        Args:
            file_path: 文件路径
            text: 原始文本
            images: 图片信息列表

        Returns:
            插入图片描述后的文本
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return cls.rebuild_for_pdf(text, images)
        elif suffix in [".docx", ".doc"]:
            return cls.rebuild_for_docx(text, images)
        else:
            return text
