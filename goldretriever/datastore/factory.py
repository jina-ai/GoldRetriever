from goldretriever.datastore.datastore import DataStore
import os


async def get_datastore() -> DataStore:
    datastore = os.environ.get("DATASTORE")
    assert datastore is not None

    match datastore:
        case "docarray":
            from goldretriever.datastore.executor.docarray_v1 import DocArrayDataStore

            return DocArrayDataStore()

        case "pinecone":
            from goldretriever.datastore import PineconeDataStore

            return PineconeDataStore()
        case "weaviate":
            from goldretriever.datastore import WeaviateDataStore

            return WeaviateDataStore()
        case "milvus":
            from goldretriever.datastore import MilvusDataStore

            return MilvusDataStore()
        case "zilliz":
            from goldretriever.datastore import ZillizDataStore

            return ZillizDataStore()
        case "redis":
            from goldretriever.datastore import RedisDataStore

            return await RedisDataStore.init()
        case "qdrant":
            from goldretriever.datastore import QdrantDataStore

            return QdrantDataStore()
        case _:
            raise ValueError(f"Unsupported vector database: {datastore}")
