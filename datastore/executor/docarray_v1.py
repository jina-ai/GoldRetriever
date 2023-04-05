import os
from typing import Dict, Any
from docarray import Document as DADoc
from jina import Executor, requests, DocumentArray
import asyncio


DEFAULT_INDEX_PATH = os.environ.get("DOCARRAY_FILE_PATH", "./retrieval_da.bin")


class DocArrayDataStore(Executor):
    def __init__(self, **kwargs):
        super().__init__()
        self._index_file_path = kwargs.get('index_file_path', DEFAULT_INDEX_PATH)
        try:
            self._index = DocumentArray.load_binary(self._index_file_path)
            print(f"Instantiated index with {len(self._index)} existing documents")
        except:
            self._index = DocumentArray()
            print(f"Instantiated empty index")

    @requests(on="/upsert")
    async def upsert(self, docs: DocumentArray, **kwargs) -> DocumentArray:
        # Delete any existing vectors for documents with the input document ids
        await asyncio.gather(self.delete(docs=docs, parameters={}))

        docs_to_append = docs[...]
        self._index.extend(docs[...])
        self._index.save_binary(self._index_file_path)
        return docs_to_append

    @requests(on="/query")
    async def query(self, docs: DocumentArray, **kwargs) -> DocumentArray:
        result_docs = DocumentArray()
        for doc in docs:  # TODO(johannes) this can probably be rewritten without the loop
            filter_query = self._get_query_from_filters(doc.tags.get('filters'))
            docs_to_search = self._index
            if filter_query:
                docs_to_search = self._index.find(filter_query)
            matches = docs_to_search.find(doc.embedding, top_k=doc.tags["top_k"])
            result_docs.append(DADoc(id=doc.id, chunks=matches))

        return result_docs

    @requests(on="/delete")
    async def delete(self, docs: DocumentArray, parameters: Dict, **kwargs) -> DocumentArray:
        delete_all = parameters.get("delete_all", False)
        ids = docs[:, "id"]
        filters = parameters.get("filters", None)
        if delete_all:
            self._index = DocumentArray()
            self._index.save_binary(self._index_file_path)
            return DocumentArray(DADoc(tags={"success": True}))
        if ids:
            del self._index[ids]
            self._index.save_binary(self._index_file_path)
            return DocumentArray(DADoc(tags={"success": True}))
        if filters:
            query = self._get_query_from_filters(filters)
            ids = self._index.find(query)[:, "id"]
            del self._index[ids]
            self._index.save_binary(self._index_file_path)
            return DocumentArray(DADoc(tags={"success": True}))
        return DocumentArray(DADoc(tags={"success": False}))

    @staticmethod
    def _get_query_from_filters(filters: Dict[str, Any]) -> Dict:
        if not filters:
            return {}
        return {'$and': [{filter: {'$eq': value}} for filter, value in filters.items()]}
