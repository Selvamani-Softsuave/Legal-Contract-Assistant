import logging
import os
from typing import Dict, Any
from processor.extractors import get_extractor_for_file
from processor.chunkers import get_chunker
from processor.services.embedding_service import ProcessorEmbeddingService
from processor.services.chroma_service import ProcessorChromaService

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    def __init__(self):
        self.embedding_service = ProcessorEmbeddingService()
        self.chroma_service = ProcessorChromaService()

    def process_document(
        self,
        document_id: str,
        contract_id: str,
        file_name: str,
        file_bytes: bytes,
        operation: str = "PROCESS"
    ) -> Dict[str, Any]:
        logger.info(f"Starting processing for document {document_id} ({file_name}), operation: {operation}")

        # If reprocessing, purge existing Chroma vectors first
        if operation in ["REPROCESS", "DELETE_INDEX"]:
            self.chroma_service.delete_document_vectors(document_id)
            if operation == "DELETE_INDEX":
                return {"status": "Deleted", "document_id": document_id, "chunks_indexed": 0}

        # 1. Extraction
        extractor = get_extractor_for_file(file_name)
        pages = extractor.extract(file_bytes)
        if not pages:
            raise ValueError(f"No text extracted from document {file_name}")

        # 2. Chunking
        chunker = get_chunker(strategy="legal", chunk_size=800, overlap=100)
        chunks = chunker.chunk(pages)
        if not chunks:
            raise ValueError(f"No chunks produced for document {file_name}")

        # 3. Embeddings
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embedding_service.get_embeddings(chunk_texts)

        # 4. Vector Indexing into ChromaDB
        indexed_count = self.chroma_service.add_chunks(
            document_id=document_id,
            contract_id=contract_id,
            document_name=file_name,
            chunks=chunks,
            embeddings=embeddings
        )

        return {
            "status": "Completed",
            "document_id": document_id,
            "contract_id": contract_id,
            "file_name": file_name,
            "page_count": len(pages),
            "chunks": chunks,
            "indexed_count": indexed_count
        }
