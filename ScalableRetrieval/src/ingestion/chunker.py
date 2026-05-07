from typing import List, Dict, Any
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


class MarkdownChunker:
    MAX_EMBEDDING_CHARS = 6000
    EMBEDDING_CHUNK_OVERLAP = 500

    def __init__(self, strategy: str = "section_aware"):
        self.strategy = strategy
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6"),
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )

        if strategy == "fixed_300_overlap_50":
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300 * 5,  # Roughly 300 words
                chunk_overlap=50 * 5,
            )
        elif strategy == "fixed_600_overlap_100":
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=600 * 5,  # Roughly 600 words
                chunk_overlap=100 * 5,
            )
        else:
            self.text_splitter = None
        self.embedding_safe_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.MAX_EMBEDDING_CHARS,
            chunk_overlap=self.EMBEDDING_CHUNK_OVERLAP,
        )

    def chunk_document(
        self,
        text: str,
        document_version_id: int,
        tenant_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        if self.strategy == "section_aware":
            documents = self.header_splitter.split_text(text)
        else:
            # For fixed size, we still might want to preserve some structure or just split raw
            documents = self.text_splitter.create_documents([text])

        chunks = []
        for doc in documents:
            # Reconstruct the structural path from metadata
            path_parts = []
            for i in range(1, 7):
                header_key = f"Header {i}"
                if header_key in doc.metadata:
                    path_parts.append(doc.metadata[header_key])

            structural_path = (
                " -> ".join(path_parts) if path_parts else "Document Root"
            )

            for text_chunk in self._split_for_embedding(doc.page_content):
                chunk = {
                    "document_version_id": document_version_id,
                    "structural_path": structural_path,
                    "text_content": text_chunk,
                }
                if tenant_id is not None:
                    chunk["tenant_id"] = tenant_id
                chunks.append(chunk)

        return chunks

    def _split_for_embedding(self, text: str) -> List[str]:
        if len(text) <= self.MAX_EMBEDDING_CHARS:
            return [text]
        return self.embedding_safe_splitter.split_text(text)
