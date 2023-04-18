# Auto ChatGPT Plugin

Effortlessly create and deploy your own ChatGPT Retrieval Plugins with `auto-chatgpt-plugin`, a powerful command-line tool that takes care of hosting and server setup for you!


## Getting Started

### Install

To get started with `auto-chatgpt-plugin`, you'll need to have Python 3.7 or later installed on your system. You can install the tool using pip:

```bash
pip install auto-chatgpt-plugin
```

### Configure
Optionally, you can configure the plugin to suit your needs by setting new values for the arguments listed in the table below:

| Argument    | Description                                   | Default Value                                                                                                                                                                                                                                    |
|:------------|:----------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name        | Name the model will use to target the plugin  | retrieval                                                                                                                                                                                                                                        |
| description | Description better tailored to the model, such as token context length considerations or keyword usage for improved plugin prompting                                      | Plugin for searching through the user's documents (such as files, emails, and more) to find answers to questions and retrieve relevant information. Use it whenever a user asks something that might be found in their personal information      |
| email       | Email contact for safety/moderation reachout, support, and deactivation                                    | hello@contact.com                                                                                                                                                                                                                                       |
| info_url    | Redirect URL for users to view plugin information                                    | hello@legal.com                                                                                                                                                                                                                                       |

Again, this step is optional, and you can continue with the default values. However, if you want to change something, run:

```bash
auto-chatgpt-plugin configure --name "my_plugin" --description "Plugin for searching through the given text documents to find answers to questions and retrieve relevant information. Use it whenever a user asks something that might be found in their personal information. Retrieve and display the relevant section of text, ensuring it does not exceed 200 words and remains unchanged."
```

Also, you can always go back to the default settings with:
```bash
auto-chatgpt-plugin configure --reset
```

### Deploy
Now, it's time to deploy it!
All you have to do is run:
```bash
auto-chatgpt-plugin deploy --key <your openai key>
```

And in a couple of seconds your plugin is deployed! 
You will get a message containing the URL of your plugin, i.e. "Gateway (Http)":
```bash
╭──────────────────────── 🎉 Flow is available! ─────────────────────────╮
│                                                                        │
│   ID               retrieval-plugin-<plugin id>                        │
│   Gateway (Http)   https://retrieval-plugin-<plugin id>.wolf.jina.ai   │
│   Dashboard        https://dashboard.wolf.jina.ai/flow/<plugin id>     │
│                                                                        │
╰────────────────────────────────────────────────────────────────────────╯
```

### Index

One last step before integrating your plugin inside ChatGPT is to index your data. Otherwise, the plugin contains no data and will not be useful.

You can collect all relevant text data (represented as txt/pdf files) in a directory:
```
-- my_files
---- text1.pdf
---- text2.pdf
---- text3.txt
...
```
and index it by running:
```bash
auto-chatgpt-plugin index --data "my_files" --id <plugin id>
```

Alternatively, you can provide text data using `docarray`:

```python
from docarray import Document, DocumentArray

texts = ['Red is a warm and bold color', 'Blue is a cool and calming color', 'Green is a refreshing and natural color']
docs = DocumentArray([Document(text=color_info) for color_info in texts])
docs.save_binary('color_docs.bin')
```

```bash
auto-chatgpt-plugin index --data "color_docs.bin" --id <plugin id>
```


### Integrate

The final step is to integrate your plugin inside ChatGPT! 
All you have to do is go to OpenAI Plugins, select "Develop your own plugin", and then "Install an unverified plugin". Provide the URL - Gateway (Http) that was given to you after deployment - and your plugin is ready to go!


### Delete

In case you want to delete your plugin, you can run:
```bash
auto-chatgpt-plugin delete <plugin id>
```