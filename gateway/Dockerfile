FROM jinaai/jina:latest

COPY . /workdir/

WORKDIR /workdir

RUN pip install -r requirements.txt

ENTRYPOINT ["jina", "gateway", "--uses", "config.yml"]