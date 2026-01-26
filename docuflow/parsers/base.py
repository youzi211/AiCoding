"""文档解析器基类和实现"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Optional


class DocumentParser(ABC):
    """文档解析器抽象基类"""

    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """解析文档并返回文本内容"""
        pass

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """检查是否支持给定的文件类型"""
        pass

    def parse_with_images(
        self,
        file_path: Path,
        extract_images: bool = False,
        describe_func: Optional[Callable[[bytes], str]] = None,
    ) -> str:
        """
        带图片提取的解析方法（可选重写）

        Args:
            file_path: 文件路径
            extract_images: 是否提取图片
            describe_func: 图片描述函数

        Returns:
            解析后的文本（可能包含图片描述）
        """
        # 默认实现：直接返回普通解析结果
        return self.parse(file_path)


class PDFParser(DocumentParser):
    """PDF 文档解析器"""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'

    def parse(self, file_path: Path) -> str:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(str(file_path))
        documents = loader.load()
        return "\n\n".join(doc.page_content for doc in documents)

    def parse_with_images(
        self,
        file_path: Path,
        extract_images: bool = False,
        describe_func: Optional[Callable[[bytes], str]] = None,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None,
    ) -> str:
        """
        解析 PDF，可选提取图片并生成描述

        Args:
            file_path: PDF 文件路径
            extract_images: 是否提取图片
            describe_func: 图片描述函数
            cache_enabled: 是否启用缓存
            cache_dir: 缓存目录路径

        Returns:
            包含文本和图片描述的内容
        """
        from docuflow.parsers.image_extractor import (
            ImageExtractor,
            TextWithImagesRebuilder,
        )

        # 先获取纯文本
        text = self.parse(file_path)

        if not extract_images:
            return text

        # 提取图片（传入缓存配置）
        cache_path = Path(cache_dir) if cache_dir else None
        extractor = ImageExtractor(use_cache=cache_enabled, cache_dir=cache_path)
        images = extractor.extract_from_file(file_path)

        if not images:
            return text

        # 生成图片描述（显示进度）
        if describe_func:
            extractor.generate_descriptions(images, describe_func, show_progress=True)

        # 将图片描述插入到文本的相应位置
        return TextWithImagesRebuilder.rebuild(file_path, text, images)


class DocxParser(DocumentParser):
    """DOCX 文档解析器"""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.docx', '.doc']

    def parse(self, file_path: Path) -> str:
        from docx2python import docx2python
        with docx2python(str(file_path)) as docx_content:
            return docx_content.text

    def parse_with_images(
        self,
        file_path: Path,
        extract_images: bool = False,
        describe_func: Optional[Callable[[bytes], str]] = None,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None,
    ) -> str:
        """
        解析 DOCX，可选提取图片并生成描述

        使用 docx2python 库，自动在图片位置插入占位符 ----image1.jpg----

        Args:
            file_path: DOCX 文件路径
            extract_images: 是否提取图片
            describe_func: 图片描述函数
            cache_enabled: 是否启用缓存
            cache_dir: 缓存目录路径

        Returns:
            包含文本和图片描述的内容
        """
        from docx2python import docx2python
        from docuflow.parsers.image_extractor import ImageExtractor, ImageInfo

        with docx2python(str(file_path)) as docx_content:
            text = docx_content.text  # 已含 ----image1.jpg---- 占位符
            images_dict = docx_content.images  # {filename: bytes}

        if not extract_images or not images_dict:
            return text

        # 转换为 ImageInfo 列表（保持 docx2python 的顺序）
        images = []
        for i, (name, img_bytes) in enumerate(images_dict.items()):
            img_format = name.split('.')[-1] if '.' in name else 'png'
            images.append(ImageInfo(
                image_data=img_bytes,
                page=None,
                index=i,
                format=img_format,
                position_hint=name,
            ))

        # 生成图片描述
        cache_path = Path(cache_dir) if cache_dir else None
        extractor = ImageExtractor(use_cache=cache_enabled, cache_dir=cache_path)
        if describe_func:
            extractor.generate_descriptions(images, describe_func, show_progress=True)

        # 替换占位符为图片描述
        # docx2python 占位符格式: ----media/image1.jpeg----
        result = text
        for img in images:
            # position_hint 就是文件名（如 image1.jpeg）
            placeholder = f"----media/{img.position_hint}----"
            if img.description:
                result = result.replace(
                    placeholder,
                    f"\n\n[图片描述: {img.description}]\n\n"
                )
            else:
                result = result.replace(placeholder, "")

        return result


class MarkdownParser(DocumentParser):
    """Markdown 文档解析器"""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.md', '.markdown']

    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding='utf-8')


class PlainTextParser(DocumentParser):
    """纯文本文档解析器"""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.txt', '.text']

    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding='utf-8')
