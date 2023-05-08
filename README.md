# Gold Retriever

Easily empower ChatGPT to store and analyze your data using `goldretriever`, a powerful command-line tool for creating and hosting retrieval plugins in just a few simple steps.


## Quick Start

### Installation

1. Ensure you have Python 3.8 or later.
2. Install the tool via pip:
  ```bash
  pip install goldretriever
  ```

### Deployment
1. Run the following command to deploy the plugin:
```bash
goldretriever deploy --key <your openai key>
```
2. Store the "Gateway (Http)" URL and the Bearer token provided in the output.
```bash
╭──────────────────────── 🎉 Flow is available! ────────────────────────╮
│                                                                       │
│   ID               retrieval-plugin-<plugin id>                       │
│   Gateway (Http)   https://retrieval-plugin-<plugin id>.wolf.jina.ai  │
│   Dashboard        https://dashboard.wolf.jina.ai/flow/<plugin id>    │
│                                                                       │
╰───────────────────────────────────────────────────────────────────────╯
Bearer token: <your bearer token>
```

### Data Indexing
1. Gather relevant text data files (PDF, TXT, DOCX, PPTX, or MD) in a directory.
2. Index the data:
```bash
goldretriever index --data my_files
```
  Or, use `docarray (v0.21.0)` for text data:
```python
from docarray import Document, DocumentArray

texts = ['Text 1', 'Text 2', 'Text 3']
docs = DocumentArray([Document(text=text) for text in texts])
docs.save_binary('docs.bin')
```
And then:
```bash
goldretriever index --data docs.bin
```

### Integration
1. Go to OpenAI Plugins.
2. Select "Develop your own plugin".
3. Enter the "Gateway (Http)" URL and Bearer token from the deployment step.


## Advanced Usage


### Configuration
To tailor the plugin to your needs, change the name and description during deployment:
```bash
goldretriever deploy --key <your openai key> --name "Custom Name" --description "Custom description"
```
If not specified, default values will be used.

| Argument    | Description                                   | Default Value                                                                                                                                                                                                                               |
|:------------|:----------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name        | Human-readable name, such as the full company name	  | Retrieval Plugin                                                                                                                                                                                                                            |
| description | Description better tailored to the model, such as token context length considerations or keyword usage for improved plugin prompting                                      | Plugin for searching through the user's documents (such as files, emails, and more) to find answers to questions and retrieve relevant information. Use it whenever a user asks something that might be found in their personal information |



### Listing Plugins
List your plugins and their status:
```bash
goldretriever list
```

Output:
```bash
Plugin ID: ece735568f | Status: Serving
```

### Deleting Plugins
Delete a plugin:
```bash
goldretriever delete <plugin id>
```

### Indexing Specific Plugins
Index data for a specific plugin:
```bash
goldretriever index --data my_files --id <plugin_id>
```
If the plugin ID is not specified, the last created plugin will be indexed.
