from src.datastore.datastore import DataStore
import os


async def get_datastore() -> DataStore:
    datastore = os.environ.get("DATASTORE")
    assert datastore is not None

    match datastore:
        case "docarray":
            from src.datastore.executor.docarray_v1 import DocArrayDataStore

            return DocArrayDataStore()

        case "pinecone":
            from src.datastore import PineconeDataStore

            return PineconeDataStore()
        case "weaviate":
            from src.datastore import WeaviateDataStore

            return WeaviateDataStore()
        case "milvus":
            from src.datastore import MilvusDataStore

            return MilvusDataStore()
        case "zilliz":
            from src.datastore import ZillizDataStore

            return ZillizDataStore()
        case "redis":
            from src.datastore import RedisDataStore

            return await RedisDataStore.init()
        case "qdrant":
            from src.datastore import QdrantDataStore

            return QdrantDataStore()
        case _:
            raise ValueError(f"Unsupported vector database: {datastore}")
