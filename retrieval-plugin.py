import os
import random
import string
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import Optional

import jwt
import typer
from hubble.api import login as login_jina
from jcloud.api import deploy as deploy_flow
from jina import Flow

from datastore.executor.docarray_v1 import DocArrayDataStore
from gateway import RetrievalGateway

app = typer.Typer()


def random_string(size=16):
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(size)
    )


def random_number(size=16):
    return int(
        "".join(random.SystemRandom().choice(string.digits) for _ in range(size))
    )


def generate_bearer_token():
    payload = {"sub": random_string(), "iat": random_number()}
    return jwt.encode(payload, "my_secret", algorithm="HS256")


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
        print(
            "Did you build the docker images? You can also use the `launch_no_docker` command to run without docker."
        )
        raise e
    with flow:
        flow.block()


@app.command()
def deploy(
    bearer_token: Optional[str] = typer.Option(None),
    openai_token: Optional[str] = typer.Option(None),
):
    args = Namespace(force=False)
    login_jina(args)

    bearer_token = bearer_token or os.environ.get("RETRIEVAL_BEARER_TOKEN")
    if not bearer_token:
        bearer_token = generate_bearer_token()
        os.environ["RETRIEVAL_BEARER_TOKEN"] = bearer_token

    openai_token = openai_token or os.environ.get("RETRIEVAL_OPENAI_TOKEN")
    if not openai_token:
        raise ValueError(
            "No OpenAI key is provided. You should either export your "
            "key as an environment variable `RETRIEVAL_OPENAI_TOKEN` or "
            "provide it through the CLI `--openai-token <your token>`"
        )

    config_str = Path("flow.yml").read_text()
    config_str = config_str.replace("<your-openai-api-key>", openai_token)
    config_str = config_str.replace("<your-bearer-token>", bearer_token)
    tmp_config_file, tmp_config_path = tempfile.mkstemp()
    try:
        with os.fdopen(tmp_config_file, "w") as tmp:
            tmp.write(config_str)
            args = Namespace(path=tmp_config_path)
        print(
            f"Your Bearer token for this deployment is - {bearer_token} - "
            f"Please store it as you will need it to interact with the plugin."
        )
        deploy_flow(args)

    finally:
        os.remove(tmp_config_path)


if __name__ == "__main__":
    app()
