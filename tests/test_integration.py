import os

from typer.testing import CliRunner
from retrieval_plugin import app

runner = CliRunner()


def test_create_plugin():
    os.environ['RETRIEVAL_OPENAI_KEY'] = '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'
    result = runner.invoke(app, ['deploy', '--key', os.environ['RETRIEVAL_OPENAI_KEY']])
    assert result.exit_code == 0
    assert 'Flow is available!' in result.stdout.strip()

