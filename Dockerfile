
FROM python:3.10 as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/


RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM jinaai/jina:3.14.0-py310

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

RUN apt-get install python3-dev

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/

ENTRYPOINT ["jina", "gateway", "--uses", "gateway/config.yml"]