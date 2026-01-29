"""文档分块和检索"""
import re
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class DocumentChunker:
    """文档分块器"""

    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )

    def chunk(self, text: str) -> list[Document]:
        """将文本分割成块"""
        return self.splitter.create_documents([text])

    def chunk_with_metadata(self, text: str, source: str) -> list[Document]:
        """将文本分割成带元数据的块"""
        docs = self.splitter.create_documents([text], metadatas=[{"source": source}])
        for i, doc in enumerate(docs):
            doc.metadata["chunk_index"] = i
        return docs


class ChunkRetriever:
    """块检索器"""

    def __init__(self, chunks: list[Document], method: str = "keyword"):
        self.chunks = chunks
        self.method = method
        self._vector_store = None

    def retrieve_keyword(self, query: str, top_k: int = 5) -> list[str]:
        """基于关键词检索"""
        keywords = re.findall(r'\w+', query.lower())
        scored_chunks = []

        for chunk in self.chunks:
            content_lower = chunk.page_content.lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scored_chunks.append((score, chunk.page_content))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = [content for _, content in scored_chunks[:top_k]]
        # 兜底：检索为空时返回前 top_k 个块
        if not results:
            results = [c.page_content for c in self.chunks[:top_k]]
        return results

    def retrieve_vector(self, query: str, top_k: int = 5) -> list[str]:
        """基于向量检索"""
        if self._vector_store is None:
            from langchain_community.vectorstores import FAISS
            from langchain_openai import AzureOpenAIEmbeddings
            from docuflow.core.config import get_settings

            settings = get_settings()
            embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_embedding_deployment or "text-embedding-ada-002",
                api_version=settings.azure_openai_api_version,
            )
            self._vector_store = FAISS.from_documents(self.chunks, embeddings)

        results = self._vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """使用配置的方法检索"""
        if self.method == "vector":
            try:
                return self.retrieve_vector(query, top_k)
            except Exception as e:
                from docuflow.utils import get_logger
                get_logger().warning(f"向量检索失败，回退到关键词: {e}")
                return self.retrieve_keyword(query, top_k)
        return self.retrieve_keyword(query, top_k)
