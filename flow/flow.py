from jina import Flow
from gateway.gateway import RetrievalGateway
from datastore.executor.docarray_v1 import DocArrayDataStore

# flow = (
#     Flow()
#     .config_gateway(uses=RetrievalGateway, port=12345, protocol="http")
#     .add(uses=DocArrayDataStore)
# )

flow = (
    Flow()
    .config_gateway(uses='docker://plugin-gateway-two', port=12345, protocol="http")
    #.add(uses='docker://filewriter-exec')
     .add(uses='docker://gpt-plugin-indexer')
)

with flow:
    flow.block()
#flow.save_config("./flow.yml")
