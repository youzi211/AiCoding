"""文档解析器基类和实现"""
from abc import ABC, abstractmethod
from pathlib import Path


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


class PDFParser(DocumentParser):
    """PDF 文档解析器"""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'

    def parse(self, file_path: Path) -> str:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(str(file_path))
        documents = loader.load()
        return "\n\n".join(doc.page_content for doc in documents)


class DocxParser(DocumentParser):
    """DOCX 文档解析器"""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.docx', '.doc']

    def parse(self, file_path: Path) -> str:
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(str(file_path))
        documents = loader.load()
        return "\n\n".join(doc.page_content for doc in documents)


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
