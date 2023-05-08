import functools
import json
import os
from typing import Dict, List, Optional

import numpy as np
import yaml
from fastapi import FastAPI, File, HTTPException, Depends, Body, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from jina.serve.runtimes.gateway.http.fastapi import FastAPIBaseGateway
from docarray import Document as DADoc, DocumentArray

from models.api import (
    DeleteRequest,
    DeleteResponse,
    QueryRequest,
    QueryResponse,
    UpsertRequest,
    UpsertResponse,
)
from models.models import (
    DocumentChunk,
    DocumentMetadataFilter,
    QueryResult,
    DocumentChunkWithScore,
    Query,
)
from services.chunks import get_document_chunks
from services.file import get_document_from_file
from services.openai import get_embeddings

bearer_scheme = HTTPBearer()
BEARER_TOKEN_ENV = os.environ.get("BEARER_TOKEN")


def validate_token(bearer_token: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials.scheme != "Bearer" or credentials.credentials != bearer_token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials


def chunk_to_dadoc(chunk: DocumentChunk) -> DADoc:
    doc = DADoc(
        text=chunk.text,
        tags=chunk.metadata.dict(),
        embedding=np.array(chunk.embedding),
    )
    if chunk.id is not None:
        doc.id = chunk.id
    return doc


def dadoc_to_chunk_with_score(doc: DADoc):
    return DocumentChunkWithScore(
        score=list(doc.scores.values())[0].value,
        id=doc.id,
        text=doc.text,
        metadata=doc.tags,
        embedding=None,
    )


def query_to_doc(query: Query, embedding: Optional[List[float]] = None) -> DADoc:
    tags = dict()
    if query.filter is not None:
        tags["filters"] = query.filter.dict()
    if query.top_k is not None:
        tags["top_k"] = query.top_k
    doc = DADoc(
        text=query.query,
        tags=tags,
    )
    if embedding is not None:
        doc.embedding = np.array(embedding)
    return doc


def doc_to_query_result(doc: DADoc) -> QueryResult:
    return QueryResult(
        query=doc.text, results=[dadoc_to_chunk_with_score(doc) for doc in doc.chunks]
    )


class RetrievalGateway(FastAPIBaseGateway):
    def __init__(self, bearer_token: Optional[str] = None, openai_token: str = '', **kwargs):
        super().__init__(**kwargs)
        self.plugin_description = kwargs.get('plugin_description')
        self.plugin_name = kwargs.get('plugin_name')
        self.bearer_token = bearer_token if bearer_token is not None else BEARER_TOKEN_ENV
        assert self.bearer_token is not None
        self.token_validation = functools.partial(validate_token, self.bearer_token)

        if openai_token:
            os.environ["OPENAI_API_KEY"] = openai_token  # TODO(johannes): hacky, change to pass around
        assert os.environ.get("OPENAI_API_KEY", None) is not None

    async def perform_upsert_call(
        self, chunks: Dict[str, List[DocumentChunk]]
    ) -> UpsertResponse:
        docs_to_send = DocumentArray()
        for _, chunk_list in chunks.items():
            docs_to_send.extend([chunk_to_dadoc(chunk) for chunk in chunk_list])
        ids_to_return = []
        async for docs in self.streamer.stream_docs(
            docs=docs_to_send,
            exec_endpoint="/upsert",
        ):
            ids_to_return.extend(docs[:, "id"])

        return UpsertResponse(ids=ids_to_return)

    async def perform_query_call(self, da: DocumentArray) -> List[QueryResult]:
        query_results = []
        async for docs in self.streamer.stream_docs(
            docs=da,
            exec_endpoint="/query",
        ):
            query_results.extend([doc_to_query_result(doc) for doc in docs])
        return query_results

    async def perform_delete_call(
        self,
        ids: Optional[List[str]] = None,
        delete_all: Optional[bool] = None,
        filter: Optional[DocumentMetadataFilter] = None,
    ) -> bool:
        ids = ids or []
        docs = DocumentArray([DADoc(id=id) for id in ids])
        parameters = {"delete_all": delete_all, "filter": filter.dict()}
        async for docs in self.streamer.stream_docs(
            docs=docs,
            parameters=parameters,
            exec_endpoint="/delete",
        ):
            if len([doc for doc in docs if doc.tags.get("success", False)]) > 0:
                return True
        return False

    def modify_config_files(self):
        # replace placeholder URL in the configuration
        with open('.well-known/ai-plugin.json', 'r') as f:
            plugin_json = json.load(f)

        plugin_json['api']['url'] = plugin_json['api']['url'].replace('<your_url>', self.url)
        plugin_json['logo_url'] = plugin_json['logo_url'].replace('<your_url>', self.url)
        if self.plugin_description:
            plugin_json['description_for_model'] = self.plugin_description
        if self.plugin_name:
            plugin_json['name_for_human'] = self.plugin_name

        with open('.well-known/ai-plugin.json', 'w') as f:
            json.dump(plugin_json, f, indent=2)

        with open('.well-known/openapi.yaml', 'r') as f:
            openapi_yaml = yaml.safe_load(f)

        openapi_yaml['info']['servers'] = self.url

        with open('.well-known/openapi.yaml', 'w') as f:
            yaml.dump(openapi_yaml, f)

    @property
    def app(self):
        app = FastAPI()
        app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")

        # construct URL
        try:
            namespace = os.environ['K8S_NAMESPACE_NAME'].split('-')[1]
        except:
            raise Exception('Could not get the namespace')

        flow_id = 'retrieval-plugin' + '-' + namespace
        self.url = f'https://{flow_id}.wolf.jina.ai'
        self.modify_config_files()

        # Create a sub-application, in order to access just the query endpoint in an OpenAPI schema, found at http://0.0.0.0:8000/sub/openapi.json when the app is running locally
        sub_app = FastAPI(
            title="Retrieval Plugin API",
            description="A retrieval API for querying and filtering documents based on natural language queries and metadata",
            version="1.0.0",
            servers=[{"url": self.url}],
            dependencies=[Depends(self.token_validation)],
        )
        app.mount("/sub", sub_app)

        @app.get("/favicon.ico")
        async def favicon():
            return FileResponse(".well-known/logo.png")

        @app.get("/openapi.yaml")
        async def read_openapi_yaml():
            return FileResponse(".well-known/openapi.yaml")

        @app.post(
            "/upsert-file",
            response_model=UpsertResponse,
            dependencies=[Depends(self.token_validation)]
        )
        async def upsert_file(
            file: UploadFile = File(...),
        ):
            document = await get_document_from_file(file)

            try:
                chunks = get_document_chunks(
                    [document], chunk_token_size=None
                )  # use default chunk size
                return await self.perform_upsert_call(chunks)
            except Exception as e:
                print("Error:", e)
                raise HTTPException(status_code=500, detail=f"str({e})")

        @app.post(
            "/upsert",
            response_model=UpsertResponse,
            dependencies=[Depends(self.token_validation)]
        )
        async def upsert(
            request: UpsertRequest = Body(...),
        ):
            try:
                chunks = get_document_chunks(
                    request.documents, chunk_token_size=None
                )  # uses default chunk size
                return await self.perform_upsert_call(chunks)
            except Exception as e:
                print("Error:", e)
                raise HTTPException(status_code=500, detail="Internal Service Error")

        @app.post(
            "/query",
            response_model=QueryResponse,
            dependencies=[Depends(self.token_validation)]
        )
        async def query_main(
            request: QueryRequest = Body(...),
        ):
            try:
                queries = request.queries
                query_texts = [query.query for query in queries]
                query_embeddings = get_embeddings(query_texts)
                query_da_docs = DocumentArray(
                    [
                        query_to_doc(query, embedding)
                        for query, embedding in zip(queries, query_embeddings)
                    ]
                )
                results = await self.perform_query_call(query_da_docs)
                return QueryResponse(results=results)

            except Exception as e:
                print("Error:", e)
                raise HTTPException(status_code=500, detail="Internal Service Error")

        @sub_app.post(
            "/query",
            response_model=QueryResponse,
            # NOTE: We are describing the shape of the API endpoint input due to a current limitation in parsing arrays of objects from OpenAPI schemas. This will not be necessary in the future.
            description="Accepts search query objects array each with query and optional filter. Break down complex questions into sub-questions. Refine results by criteria, e.g. time / source, don't do this often. Split queries if ResponseTooLargeError occurs.",
            dependencies=[Depends(self.token_validation)],
        )
        async def query(
            request: QueryRequest = Body(...),
        ):
            try:
                queries = request.queries
                query_texts = [query.query for query in queries]
                query_embeddings = get_embeddings(query_texts)
                query_da_docs = DocumentArray(
                    [
                        query_to_doc(query, embedding)
                        for query, embedding in zip(queries, query_embeddings)
                    ]
                )
                results = await self.perform_query_call(query_da_docs)
                return QueryResponse(results=results)
            except Exception as e:
                print("Error:", e)
                raise HTTPException(status_code=500, detail="Internal Service Error")

        @app.delete(
            "/delete",
            response_model=DeleteResponse,
            dependencies=[Depends(self.token_validation)]
        )
        async def delete(
            request: DeleteRequest = Body(...),
        ):
            if not (request.ids or request.filter or request.delete_all):
                raise HTTPException(
                    status_code=400,
                    detail="One of ids, filter, or delete_all is required",
                )
            try:
                success = self.perform_delete_call(
                    request.ids, request.delete_all, request.filter
                )
                return DeleteResponse(success=success)
            except Exception as e:
                print("Error:", e)
                raise HTTPException(status_code=500, detail="Internal Service Error")

        return app
