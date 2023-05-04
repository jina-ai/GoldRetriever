from auto_retrieval_plugin.datastore.datastore import DataStore
import os


async def get_datastore() -> DataStore:
    datastore = os.environ.get("DATASTORE")
    assert datastore is not None

    match datastore:
        case "docarray":
            from auto_retrieval_plugin.datastore.executor.docarray_v1 import DocArrayDataStore

            return DocArrayDataStore()

        case "pinecone":
            from auto_retrieval_plugin.datastore import PineconeDataStore

            return PineconeDataStore()
        case "weaviate":
            from auto_retrieval_plugin.datastore import WeaviateDataStore

            return WeaviateDataStore()
        case "milvus":
            from auto_retrieval_plugin.datastore import MilvusDataStore

            return MilvusDataStore()
        case "zilliz":
            from auto_retrieval_plugin.datastore import ZillizDataStore

            return ZillizDataStore()
        case "redis":
            from auto_retrieval_plugin.datastore import RedisDataStore

            return await RedisDataStore.init()
        case "qdrant":
            from auto_retrieval_plugin.datastore import QdrantDataStore

            return QdrantDataStore()
        case _:
            raise ValueError(f"Unsupported vector database: {datastore}")
