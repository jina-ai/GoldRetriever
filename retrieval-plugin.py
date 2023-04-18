import asyncio
import json
import os
import random
import shutil
import string
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import Optional

import jwt
import requests
import typer
from docarray import DocumentArray
from hubble.api import login as login_jina
from jcloud.api import deploy as deploy_flow
from jcloud.flow import CloudFlow
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


def write_envs(new_envs):
    old_envs = {}
    if os.path.exists('.env'):
        with open(".env", "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                old_envs[key] = value

    env_vars = {**old_envs, **new_envs}

    with open(".env", "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


def read_envs():
    if os.path.exists('.env'):
        with open(".env", "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                os.environ[key] = value


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


def create_eventloop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return asyncio.get_event_loop()


@app.command()
def index(
    file: str = typer.Option,
    bearer_token: Optional[str] = typer.Option(None),
    flow_id: Optional[str] = typer.Option(None),
):
    read_envs()
    flow_id = flow_id or os.environ["RETRIEVAL_FLOW_ID"]
    if not flow_id:
        raise ValueError(
            "Flow ID is not provided. You should either export your "
            "flow ID as an environment variable `RETRIEVAL_FLOW_ID` or "
            "provide it through the CLI `--flow-id <your-flow-id>`"
        )

    bearer_token = bearer_token or os.environ.get("RETRIEVAL_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError(
            "No Bearer token is provided. You should either export your "
            "token as an environment variable `RETRIEVAL_BEARER_TOKEN` or "
            "provide it through the CLI `--bearer-token <your token>`"
        )

    if not os.path.exists(file):
        raise FileNotFoundError(f'{file} does not exist')

    endpoint_url = f"https://{flow_id}-http.wolf.jina.ai/upsert"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }
    file = {'file': open(file, 'rb')}

    response = requests.post(endpoint_url, headers=headers, files=file)
    print(response.json())


@app.command()
def delete(plugin_id: str):
    flow_id = 'retrieval-plugin-' + plugin_id
    CloudFlow(flow_id=flow_id).__exit__()
    print(f'Plugin {plugin_id} was successfully deleted')


@app.command()
def configure(
    name: str = typer.Option(None),
    description: str = typer.Option(None),
    email: str = typer.Option(None),
    info_url: str = typer.Option(None),
    reset: bool = typer.Option(False)
):
    if reset:
        shutil.copy('.well-known/default-ai-plugin.json', '.well-known/ai-plugin.json')
        print('Default configuration has been loaded')
        return

    with open('.well-known/ai-plugin.json', 'r') as f:
        config = json.load(f)

    if name:
        config['name_for_model'] = name
    if description:
        config['description_for_model'] = description
    if email:
        config['contact_email'] = email
    if info_url:
        config['legal_info_url'] = info_url

    if name or description or email or info_url:
        with open('.well-known/ai-plugin.json', 'w') as f:
            json.dump(config, f, indent=2)
        print('Configuration has been successfully updated')
    else:
        print('Configuration has not been changed')


@app.command()
def index_docs(
    docs: str = typer.Option,
    bearer_token: Optional[str] = typer.Option(None),
    flow_id: Optional[str] = typer.Option(None),
):
    read_envs()
    flow_id = flow_id or os.environ["RETRIEVAL_FLOW_ID"]
    if not flow_id:
        raise ValueError(
            "Flow ID is not provided. You should either export your "
            "flow ID as an environment variable `RETRIEVAL_FLOW_ID` or "
            "provide it through the CLI `--flow-id <your-flow-id>`"
        )

    bearer_token = bearer_token or os.environ.get("RETRIEVAL_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError(
            "No Bearer token is provided. You should either export your "
            "token as an environment variable `RETRIEVAL_BEARER_TOKEN` or "
            "provide it through the CLI `--bearer-token <your token>`"
        )

    endpoint_url = f"https://{flow_id}.wolf.jina.ai/upsert"
    # endpoint_url = 'https://chatgpt-retrieval-plugin.jina.ai/upsert'
    print(endpoint_url)
    if os.path.exists(docs):
        docs = DocumentArray.load_binary(docs)
    else:
        try:
            docs = DocumentArray.pull(docs)
        except:
            raise Exception('Could not find documents')

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }
    data = {"documents": []}
    for ind, doc in enumerate(docs):
        data["documents"].append({
                "id": str(ind),
                "text": doc.text,
                "metadata": {
                    "source": doc.tags.get("source", "email"),
                    "source_id": doc.tags.get("source_id", "string"),
                    "url": doc.tags.get("url", "string"),
                    "created_at": doc.tags.get("created_at", "string"),
                    "author": doc.tags.get("author", "string"),
                },
            })
    response = requests.post(endpoint_url, headers=headers, json=data)
    print(response.json())


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

    read_envs()
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
        flow = deploy_flow(args)

        write_envs(
            {
                "RETRIEVAL_BEARER_TOKEN": bearer_token,
                "RETRIEVAL_FLOW_ID": flow.flow_id,
                "RETRIEVAL_OPENAI_TOKEN": openai_token,
            }
        )

    finally:
        os.remove(tmp_config_path)


if __name__ == "__main__":
    app()
