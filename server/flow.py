from jina import Flow
from server.main import RetrievalGateway
from datastore.providers.docarray_v1 import DocArrayDataStore

flow = (
    Flow()
    .config_gateway(uses=RetrievalGateway, port=12345, protocol="http")
    .add(uses=DocArrayDataStore)
)

with flow:
    flow.block()
