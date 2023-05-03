import os

from typer.testing import CliRunner
from retrieval_plugin import app, get_flows
from unittest.mock import patch

runner = CliRunner()


@patch('retrieval_plugin.FLOW_PATH', 'tests/resources/test_flow.yml')
def test_create_plugin():
    result = runner.invoke(app, ['deploy', '--key', os.environ['RETRIEVAL_OPENAI_KEY']])
    assert 'Flow is available!' in result.stdout.strip()

    flows = get_flows(keyword='test-retrieval')
    assert len(flows) == 1

    flow_id = flows[0]['id']
    assert os.environ['RETRIEVAL_FLOW_ID'] == flow_id

    runner.invoke(app, ['index', '--data', 'tests/resources/text_data/'])

    result = runner.invoke(app, ['query', 'blue'])
    assert 'Blue is a primary color' in result.stdout.strip()

    result = runner.invoke(app, ['delete', flow_id])
    assert 'was successfully deleted' in result.stdout.strip()



import subprocess


def test_retrieval_plugin_deploy():
    command = f"retrieval-plugin deploy --key {os.environ['RETRIEVAL_OPENAI_KEY']}"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        print("Command executed successfully.")
        print("Output:", result.stdout)
    else:
        print("Command execution failed.")
        print("Error:", result.stderr)

    assert result.returncode == 0, f"Command execution failed. Error: {result.stderr}"
