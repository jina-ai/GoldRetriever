import os
from argparse import Namespace
from typing import Optional
from jina import Flow
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


@app.command()
def deploy(bearer_token: Optional[str], openai_token: Optional[str]):
    from pathlib import Path
    from jcloud.api import deploy as deploy_flow
    import tempfile
    from hubble.api import login as login_jina

    args = Namespace(force=False)
    login_jina(args)

    config_str = Path('flow.yml').read_text()
    config_str = config_str.replace('<your-openai-api-key>', openai_token)
    config_str = config_str.replace('<your-bearer-token>', bearer_token)
    tmp_config_file, tmp_config_path = tempfile.mkstemp()
    try:
        with os.fdopen(tmp_config_file, 'w') as tmp:
            tmp.write(config_str)
            args = Namespace(path=tmp_config_path)
        deploy_flow(args)

    finally:
        os.remove(tmp_config_path)


if __name__ == "__main__":
    app()
