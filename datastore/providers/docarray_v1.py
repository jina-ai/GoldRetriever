import os
from typing import Dict, List, Optional

import numpy as np
from docarray import DocumentArray
from docarray import Document as DADoc

from datastore.datastore import DataStore
from models.models import (
    DocumentChunk,
    DocumentMetadataFilter,
    QueryResult,
    QueryWithEmbedding,
    DocumentChunkWithScore,
)

DOCARRAY_FILE_PATH = os.environ.get("DOCARRAY_FILE_PATH", "./retrieval_da.bin")


class DocArrayDataStore(DataStore):
    def __init__(self):
        super().__init__()
        try:
            self._data = DocumentArray.load_binary(DOCARRAY_FILE_PATH)
        except:
            self._data = DocumentArray()

    async def _upsert(self, chunks: Dict[str, List[DocumentChunk]]) -> List[str]:
        """
        Takes in a list of list of document chunks and inserts them into the database.
        Return a list of document ids.
        """
        docs_to_append = DocumentArray()
        for _, chunk_list in chunks.items():
            for chunk in chunk_list:
                docs_to_append.append(self.chunk_to_dadoc(chunk))
        self._data.extend(docs_to_append)
        self._data.save_binary(DOCARRAY_FILE_PATH)
        return docs_to_append[:, "id"]

    def chunk_to_dadoc(self, chunk: DocumentChunk) -> DADoc:
        doc = DADoc(
            text=chunk.text,
            tags=chunk.metadata.dict(),
            embedding=np.array(chunk.embedding),
        )
        if chunk.id is not None:
            doc.id = chunk.id
        return doc

    async def _query(self, queries: List[QueryWithEmbedding]) -> List[QueryResult]:
        """
        Takes in a list of queries with embeddings and filters and returns a list of query results with matching document chunks and scores.
        """
        results = []
        for query in queries:
            embedding = np.array(query.embedding)
            # filter = ... # TODO(johanens) support filters. For now they are ignored.
            result_docs = self._data.find(embedding, top_k=query.top_k)
            results.append(
                QueryResult(
                    query=query.query,
                    results=[
                        self.dadoc_to_chunk_with_score(doc) for doc in result_docs
                    ],
                )
            )
        return results

    def dadoc_to_chunk_with_score(self, doc: DADoc):
        return DocumentChunkWithScore(
            score=list(doc.scores.values())[0].value,
            id=doc.id,
            text=doc.text,
            metadata=doc.tags,
            embedding=list(doc.embedding),
        )

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[DocumentMetadataFilter] = None,
        delete_all: Optional[bool] = None,
    ) -> bool:
        """
        Removes vectors by ids, filter, or everything in the datastore.
        Multiple parameters can be used at once.
        Returns whether the operation was successful.
        """
        if delete_all:
            self._data = DocumentArray()
            self._data.save_binary(DOCARRAY_FILE_PATH)
            return True
        if ids is not None:
            del self._data[ids]
            self._data.save_binary(DOCARRAY_FILE_PATH)
            return True
        # TODO(johanens) support filters. For now they are ignored.
        return False
