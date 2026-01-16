"""文档解析器工厂"""
from pathlib import Path
from typing import Optional

from docuflow.parsers.base import (
    DocumentParser, PDFParser, DocxParser,
    MarkdownParser, PlainTextParser
)


class DocumentParserFactory:
    """文档解析器工厂"""

    def __init__(self):
        self._parsers = [
            PDFParser(),
            DocxParser(),
            MarkdownParser(),
            PlainTextParser(),
        ]

    def get_parser(self, file_path: Path) -> Optional[DocumentParser]:
        """获取适合给定文件的解析器"""
        for parser in self._parsers:
            if parser.supports(file_path):
                return parser
        return None

    def parse(self, file_path: Path) -> str:
        """使用适当的解析器解析文档"""
        parser = self.get_parser(file_path)
        if not parser:
            raise ValueError(f"不支持的文件类型: {file_path.suffix}")
        return parser.parse(file_path)
