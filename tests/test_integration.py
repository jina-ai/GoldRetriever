import os

from typer.testing import CliRunner
from retrieval_plugin import app, get_flows
from unittest.mock import patch

runner = CliRunner()


@patch('retrieval_plugin.FLOW_PATH', 'tests/resources/test_flow.yml')
def test_create_plugin():
    os.environ['RETRIEVAL_OPENAI_KEY'] = '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'
    result = runner.invoke(app, ['deploy', '--key', os.environ['RETRIEVAL_OPENAI_KEY']])
    assert result.exit_code == 0
    assert 'Flow is available!' in result.stdout.strip()

    flows = get_flows(keyword='test-retrieval')
    assert len(flows) == 1

    flow_id = flows[0]['id']
    assert os.environ['RETRIEVAL_FLOW_ID'] == flow_id

    runner.invoke(app, ['index', '--data', 'tests/resources/text_data/'])

    result = runner.invoke(app, ['query', 'blue'])
    assert 'Blue is a primary color' in result.stdout.strip()

    result = runner.invoke(app, ['delete', '--id', flow_id])
    assert 'was successfully deleted' in result.stdout.strip()



