FROM jinaai/jina:3.14.1-py310-standard

COPY . /executor_root/

WORKDIR /executor_root

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]