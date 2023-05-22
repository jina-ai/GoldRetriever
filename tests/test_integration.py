import os
import unittest
from unittest.mock import patch

from typer.testing import CliRunner
from goldretriever.retriever import app, get_flows
import time

class TestRetriever(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.key = os.environ['RETRIEVAL_OPENAI_KEY']
        self.test_flow_path = 'tests/resources/test_flow.yml'
        os.environ['JCLOUD_NO_SURVEY'] = 'no_survey_please'

    @patch('goldretriever.retriever.FLOW_PATH', 'tests/resources/test_flow.yml')
    def test_create_plugin(self):
        result = self.runner.invoke(app, ['deploy', '--key', self.key])
        self.assertIn('Flow is available!', result.stdout.strip())
        time.sleep(5)
        flows = get_flows(keyword='test-retrieval')
        self.assertEqual(len(flows), 1)

        flow_id = flows[0]['id']
        self.assertEqual(os.environ['RETRIEVAL_FLOW_ID'], flow_id)

        self.runner.invoke(app, ['index', '--data', 'tests/resources/text_data/'])

        result = self.runner.invoke(app, ['query', 'blue'])
        self.assertIn('Blue is a primary color', result.stdout.strip())

        result = self.runner.invoke(app, ['delete', flow_id])
        self.assertIn('was successfully deleted', result.stdout.strip())

if __name__ == '__main__':
    unittest.main()
