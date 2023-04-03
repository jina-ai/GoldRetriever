import os
from typing import Optional
from jina import Flow
from jina.excepts import BadImageNameError, RuntimeFailToStart
from gateway import RetrievalGateway
from datastore.executor.docarray_v1 import DocArrayDataStore

import typer

app = typer.Typer()


@app.command()
def launch_no_docker(bearer_token: Optional[str], openai_token: Optional[str]):
    flow = (
        Flow()
        .config_gateway(
            uses=RetrievalGateway,
            port=12345,
            protocol="http",
            uses_with={"bearer_token": bearer_token, "openai_token": openai_token},
        )
        .add(uses=DocArrayDataStore)
    )

    with flow:
        flow.block()


@app.command()
def launch(bearer_token: Optional[str], openai_token: Optional[str]):
    openai_key = (
        openai_token if openai_token is not None else os.environ.get("OPENAI_API_KEY")
    )
    bearer = (
        bearer_token if bearer_token is not None else os.environ.get("BEARER_TOKEN")
    )

    try:
        flow = (
            Flow()
            .config_gateway(
                uses="docker://plugin-gateway-two",
                port=12345,
                protocol="http",
                env={"OPENAI_API_KEY": openai_key, "BEARER_TOKEN": bearer},
            )
            .add(uses="docker://gpt-plugin-indexer")
        )
    except Exception as e:
        print('Did you build the docker images? You can also use the `launch_no_docker` command to run without docker.')
        raise e
    with flow:
        flow.block()


if __name__ == "__main__":
    app()
