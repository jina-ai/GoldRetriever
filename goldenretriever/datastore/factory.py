from goldenretriever.datastore.datastore import DataStore
import os


async def get_datastore() -> DataStore:
    datastore = os.environ.get("DATASTORE")
    assert datastore is not None

    match datastore:
        case "docarray":
            from goldenretriever.datastore.executor.docarray_v1 import DocArrayDataStore

            return DocArrayDataStore()

        case "pinecone":
            from goldenretriever.datastore import PineconeDataStore

            return PineconeDataStore()
        case "weaviate":
            from goldenretriever.datastore import WeaviateDataStore

            return WeaviateDataStore()
        case "milvus":
            from goldenretriever.datastore import MilvusDataStore

            return MilvusDataStore()
        case "zilliz":
            from goldenretriever.datastore import ZillizDataStore

            return ZillizDataStore()
        case "redis":
            from goldenretriever.datastore import RedisDataStore

            return await RedisDataStore.init()
        case "qdrant":
            from goldenretriever.datastore import QdrantDataStore

            return QdrantDataStore()
        case _:
            raise ValueError(f"Unsupported vector database: {datastore}")
