"""文档解析器工厂"""
from pathlib import Path
from typing import Callable, Optional

from docuflow.parsers.base import (
    DocumentParser, PDFParser, DocxParser,
    MarkdownParser, PlainTextParser
)


def clean_text(text: str) -> str:
    """
    清理解析后的文本，移除多余的空行和空格

    使用 textacy 库的预处理功能

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    from textacy import preprocessing
    return preprocessing.normalize.whitespace(text)


class DocumentParserFactory:
    """文档解析器工厂"""

    def __init__(
        self,
        extract_images: bool = False,
        vision_model: Optional[str] = None,
        vision_max_tokens: int = 2000,
        vision_cache_enabled: bool = True,
        vision_cache_dir: Optional[str] = None
    ):
        """
        初始化解析器工厂

        Args:
            extract_images: 是否提取文档中的图片
            vision_model: 用于生成图片描述的视觉模型名称（如 "gpt-4-vision"）
            vision_max_tokens: 图片描述的最大 token 数
            vision_cache_enabled: 是否启用图片描述缓存
            vision_cache_dir: 图片描述缓存目录路径
        """
        self.extract_images = extract_images
        self.vision_model = vision_model
        self.vision_max_tokens = vision_max_tokens
        self.vision_cache_enabled = vision_cache_enabled
        self.vision_cache_dir = vision_cache_dir
        self._parsers = [
            PDFParser(),
            DocxParser(),
            MarkdownParser(),
            PlainTextParser(),
        ]
        self._describe_func: Optional[Callable[[bytes], str]] = None

    def get_parser(self, file_path: Path) -> Optional[DocumentParser]:
        """获取适合给定文件的解析器"""
        for parser in self._parsers:
            if parser.supports(file_path):
                return parser
        return None

    def _get_describe_func(self) -> Optional[Callable[[bytes], str]]:
        """获取图片描述函数（延迟加载）"""
        if self.extract_images and self.vision_model and self._describe_func is None:
            from docuflow.llm.vision_client import create_vision_description_function

            self._describe_func = create_vision_description_function(
                model_name=self.vision_model,
                max_tokens=self.vision_max_tokens
            )
        return self._describe_func

    def parse(self, file_path: Path) -> str:
        """
        使用适当的解析器解析文档

        Args:
            file_path: 文件路径

        Returns:
            解析后的文本内容
        """
        parser = self.get_parser(file_path)
        if not parser:
            raise ValueError(f"不支持的文件类型: {file_path.suffix}")
        text = parser.parse(file_path)
        return clean_text(text)

    def parse_with_images(self, file_path: Path) -> str:
        """
        使用适当的解析器解析文档，包含图片提取和描述

        Args:
            file_path: 文件路径

        Returns:
            包含文本和图片描述的内容
        """
        parser = self.get_parser(file_path)
        if not parser:
            raise ValueError(f"不支持的文件类型: {file_path.suffix}")

        # 如果解析器支持 parse_with_images 方法
        if hasattr(parser, 'parse_with_images'):
            describe_func = self._get_describe_func()
            text = parser.parse_with_images(
                file_path,
                extract_images=self.extract_images,
                describe_func=describe_func,
                cache_enabled=self.vision_cache_enabled,
                cache_dir=self.vision_cache_dir
            )
            return clean_text(text)

        # 默认回退到普通解析
        text = parser.parse(file_path)
        return clean_text(text)
