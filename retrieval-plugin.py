from typing import Optional
from jina import Flow
from gateway.gateway import RetrievalGateway
from datastore.executor.docarray_v1 import DocArrayDataStore

import typer

app = typer.Typer()


@app.command()
def launch(bearer_token: Optional[str], openai_token: Optional[str]):

    flow = (
        Flow()
        .config_gateway(uses=RetrievalGateway, port=12345, protocol="http", uses_with={'bearer_token': bearer_token, 'openai_token': openai_token})
        .add(uses=DocArrayDataStore)
    )

    with flow:
        flow.block()


if __name__ == "__main__":
    app()
