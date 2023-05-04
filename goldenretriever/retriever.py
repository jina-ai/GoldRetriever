import asyncio
import glob
import mimetypes
import os
import random
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

app = typer.Typer()

current_file_path = Path(__file__).resolve()
FLOW_PATH = current_file_path.parent / "flow.yml"
ENV_FILE_PATH = current_file_path.parent / ".env"


class UnsupportedExtensionError(Exception):
    pass


class EmptyDirectoryError(Exception):
    pass


class DataSourceNotFoundError(Exception):
    pass


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
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                old_envs[key] = value

    env_vars = {**old_envs, **new_envs}

    with open(ENV_FILE_PATH, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
            os.environ[key] = value


def read_envs():
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                os.environ[key] = value


def check_bearer_token(bearer_token: Optional[str] = None, generate: Optional[bool] = False):
    bearer_token = bearer_token or os.environ.get("RETRIEVAL_BEARER_TOKEN")
    if not bearer_token:
        if generate:
            bearer_token = generate_bearer_token()
            os.environ["RETRIEVAL_BEARER_TOKEN"] = bearer_token
        else:
            raise ValueError(
                "No Bearer token is provided. You should either export your "
                "token as an environment variable `RETRIEVAL_BEARER_TOKEN` or "
                "provide it through the CLI `--bearer-token <your token>`"
            )
    return bearer_token


def check_flow_id(flow_id: Optional[str] = None):
    flow_id = flow_id or os.environ.get("RETRIEVAL_FLOW_ID")
    if not flow_id:
        raise ValueError(
            "Flow ID is not provided. You should either export your "
            "flow ID as an environment variable `RETRIEVAL_FLOW_ID` or "
            "provide it through the CLI `--flow-id <your-flow-id>`"
        )
    elif "retrieval" not in flow_id:
        flow_id = f"retrieval-plugin-{flow_id}"
    return flow_id


def check_openai_key(openai_key: Optional[str] = None):
    openai_key = openai_key or os.environ.get("RETRIEVAL_OPENAI_KEY")
    if not openai_key:
        raise ValueError(
            "No OpenAI key is provided. You should either export your "
            "key as an environment variable `RETRIEVAL_OPENAI_KEY` or "
            "provide it through the CLI `--openai-key <your key>`"
        )
    return openai_key


def upsert_documents(docs, bearer_token, flow_id, n_docs=5):
    print(f"Indexing documents into {flow_id}")
    endpoint_url = f"https://{flow_id}.wolf.jina.ai/upsert"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }
    for batch in range(0, len(docs), n_docs):
        data = {"documents": []}
        for ind, doc in enumerate(docs[batch : batch + n_docs]):
            data["documents"].append(
                {
                    "id": str(batch + ind),
                    "text": doc.text,
                    "metadata": {
                        "source": doc.tags.get("source", "email"),
                        "source_id": doc.tags.get("source_id", "string"),
                        "url": doc.tags.get("url", "string"),
                        "created_at": doc.tags.get("created_at", "string"),
                        "author": doc.tags.get("author", "string"),
                    },
                }
            )
        response = requests.post(endpoint_url, headers=headers, json=data)
        if response.status_code != 200:
            print("Could not index the documents")
            print(response.text)


def upsert_files(files, bearer_token, flow_id):
    print(f"Indexing files into {flow_id}")
    endpoint_url = f"https://{flow_id}.wolf.jina.ai/upsert-file"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
    }
    for file in files:
        print(f"Indexing {file}")
        files = {"file": (file, open(file, "rb"), mimetypes.guess_type(file)[0])}
        response = requests.post(endpoint_url, headers=headers, files=files)
        if response.status_code != 200:
            print("Could not index the file")
            print(response.text)


@app.command()
def index(
    data: str = typer.Option,
    bearer_token: Optional[str] = typer.Option(None),
    id: Optional[str] = typer.Option(None),
):
    read_envs()
    bearer_token = check_bearer_token(bearer_token)
    flow_id = check_flow_id(id)

    docs, files = DocumentArray(), []

    # check if data is a file
    if os.path.isfile(data):
        extension = os.path.splitext(data)[-1]

        if extension == ".bin":
            docs.extend(DocumentArray.load_binary(data))
        elif extension in [".txt", ".pdf", ".docx", ".pptx", ".md"]:
            files.append(data)
        else:
            raise UnsupportedExtensionError(
                f"Can not send {extension} file. Supported extensions: text data [txt, pdf, docx, pptx, md], docarray file [.bin]"
            )

    # check if data is a directory
    elif os.path.isdir(data):
        for file in glob.glob(os.path.join(data, "*")):
            extension = os.path.splitext(file)[-1]

            if extension == ".bin":
                docs.extend(DocumentArray.load_binary(file))
            elif extension in [".txt", ".pdf", ".docx", ".pptx", ".md"]:
                files.append(file)

        if not docs and not files:
            raise EmptyDirectoryError(
                f"{data} does not contain neither text data [txt, pdf, docx, pptx, md] nor docarray files [.bin]"
            )

    else:
        try:
            docs = DocumentArray.pull(data)
        except:
            raise DataSourceNotFoundError(f"Could not find {data}")

    if docs:
        upsert_documents(docs, bearer_token, flow_id)

    if files:
        upsert_files(files, bearer_token, flow_id)


def create_eventloop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return asyncio.get_event_loop()


def get_flows(keyword='retrieval-plugin'):
    phases = "Serving,Failed,Pending,Starting,Updating,Paused"
    loop = create_eventloop()
    jflows = loop.run_until_complete(CloudFlow().list_all(phase=phases))["flows"]
    retrieval_flows = [flow for flow in jflows if keyword in flow["id"]]
    return retrieval_flows


@app.command()
def list():
    jflows = get_flows()
    for flow in jflows:
        id = flow["id"].split("-")[-1]
        print(f"Plugin ID: {id} | Status: {flow['status']['phase']}")


@app.command()
def delete(plugin_id: str):
    flow_id = "retrieval-plugin-" + plugin_id if 'retrieval' not in plugin_id else plugin_id
    jflow_ids = [flow["id"] for flow in get_flows(keyword='retrieval')]
    if flow_id in jflow_ids:
        CloudFlow(flow_id=flow_id).__exit__()
        print(f"{plugin_id} was successfully deleted")
    else:
        print(f"{plugin_id} does not exist")


@app.command()
def query(
    query: str,
    id: Optional[str] = typer.Option(None),
    bearer_token: Optional[str] = typer.Option(None),
):
    read_envs()
    bearer_token = check_bearer_token(bearer_token)
    flow_id = check_flow_id(id)
    print(f'Querying "{query}" to {flow_id}')
    endpoint_url = f"https://{flow_id}.wolf.jina.ai/query"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }
    data = {"queries": [{"query": query, "top_k": 1}]}

    response = requests.post(endpoint_url, headers=headers, json=data)
    if 'results' in response.json():
        results = response.json()["results"][0]["results"]
        for ind, res in enumerate(results):
            print(ind, res["text"][:150] + "...")
    else:
        print(response.json())


@app.command()
def deploy(
    bearer_token: Optional[str] = typer.Option(None),
    key: Optional[str] = typer.Option(None),
    description: Optional[str] = typer.Option(''),
    name: Optional[str] = typer.Option(''),
):
    args = Namespace(force=False)
    login_jina(args)

    read_envs()
    bearer_token = check_bearer_token(bearer_token, generate=True)
    openai_key = check_openai_key(key)

    config_str = Path(FLOW_PATH).read_text()
    config_str = config_str.replace("<your-openai-api-key>", openai_key)
    config_str = config_str.replace("<your-bearer-token>", bearer_token)
    config_str = config_str.replace("<plugin-description>", description)
    config_str = config_str.replace("<plugin-name>", name)
    tmp_config_file, tmp_config_path = tempfile.mkstemp()
    try:
        with os.fdopen(tmp_config_file, "w") as tmp:
            tmp.write(config_str)
            args = Namespace(path=tmp_config_path)
        flow = deploy_flow(args)
        print(
            f"Bearer token: {bearer_token}"
        )

        write_envs(
            {
                "RETRIEVAL_BEARER_TOKEN": bearer_token,
                "RETRIEVAL_FLOW_ID": flow.flow_id,
                "RETRIEVAL_OPENAI_KEY": openai_key,
            }
        )

    finally:
        os.remove(tmp_config_path)


if __name__ == "__main__":
    app()
