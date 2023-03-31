import os
from typing import Dict, List

from docarray import Document as DADoc

from jina import Executor, requests, DocumentArray

from models.models import (
    DocumentChunk,
)


DOCARRAY_FILE_PATH = os.environ.get("DOCARRAY_FILE_PATH", "./retrieval_da.bin")


def da_to_doc_chunks(da: DocumentArray) -> List[DocumentChunk]:
    chunks = []
    for doc in da:
        chunks.append(
            DocumentChunk(
                text=doc.text,
                metadata=doc.tags,
                embedding=list(doc.embedding),
                id=doc.id,
            )
        )
    return chunks


class DocArrayDataStore(Executor):
    def __init__(self, **kwargs):
        super().__init__()
        try:
            self._index = DocumentArray.load_binary(DOCARRAY_FILE_PATH)
            print(f"Instantiated index with {len(self._index)} existing documents")
        except:
            self._index = DocumentArray()
            print(f"Instantiated empty index")

    @requests(on="/upsert")
    async def upsert(self, docs: DocumentArray, **kwargs) -> DocumentArray:
        # Delete any existing vectors for documents with the input document ids
        # TODO(johannes) re-enable this filtering delete here
        # await asyncio.gather(
        #     *[
        #         self.delete(
        #             filter=DocumentMetadataFilter(
        #                 document_id=document.id,
        #             ),
        #             delete_all=False,
        #         )
        #         for document in documents
        #         if document.id
        #     ]
        # )

        docs_to_append = docs[...]
        self._index.extend(docs[...])
        self._index.save_binary(DOCARRAY_FILE_PATH)
        return docs_to_append

    @requests(on="/query")
    async def query(self, docs: DocumentArray, **kwargs) -> DocumentArray:
        result_docs = DocumentArray()
        for (
            doc
        ) in docs:  # TODO(johannes) this can probably be rewritten without the loop
            # filter = ... # TODO(johannes) support filters. For now they are ignored.
            matches = self._index.find(doc.embedding, top_k=doc.tags["top_k"])
            result_docs.append(DADoc(id=doc.id, chunks=matches))

        return result_docs

    @requests(on="/delete")
    async def delete(self, docs: DocumentArray, parameters: Dict, **kwargs) -> DocumentArray:
        delete_all = parameters.get("delete_all", False)
        ids = docs[:, "id"]
        filters = parameters.get("filters", None)
        if delete_all:
            self._index = DocumentArray()
            self._index.save_binary(DOCARRAY_FILE_PATH)
            return DocumentArray(DADoc(tags={"success": True}))
        if ids:
            del self._index[ids]
            self._index.save_binary(DOCARRAY_FILE_PATH)
            return DocumentArray(DADoc(tags={"success": True}))
        # TODO(johanens) support filters. For now they are ignored.
        return DocumentArray(DADoc(tags={"success": False}))
