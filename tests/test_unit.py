import os
import unittest

from goldretriever.retriever import check_bearer_token, check_flow_id, check_openai_key


class TestCheckFunctions(unittest.TestCase):

    def test_check_bearer_token(self):
        os.environ['RETRIEVAL_BEARER_TOKEN'] = 'my_bearer_token'

        bearer_token = check_bearer_token()
        self.assertEqual(bearer_token, 'my_bearer_token')

        bearer_token = check_bearer_token(bearer_token='my_new_bearer_token')
        self.assertEqual(bearer_token, 'my_new_bearer_token')

        os.environ.pop('RETRIEVAL_BEARER_TOKEN')
        bearer_token = check_bearer_token(generate=True)
        self.assertIsNotNone(bearer_token)

        os.environ.pop('RETRIEVAL_BEARER_TOKEN', None)
        with self.assertRaises(ValueError, msg='No Bearer token is provided'):
            check_bearer_token()

    def test_check_flow_id(self):
        os.environ['RETRIEVAL_FLOW_ID'] = 'abcdefghijk'
        flow_id = check_flow_id()
        self.assertEqual(flow_id, 'retrieval-plugin-abcdefghijk')

        flow_id = check_flow_id('new_id')
        self.assertEqual(flow_id, 'retrieval-plugin-new_id')

        flow_id = check_flow_id('retrieval-plugin-123445667')
        self.assertEqual(flow_id, 'retrieval-plugin-123445667')

        os.environ.pop('RETRIEVAL_FLOW_ID', None)
        with self.assertRaises(ValueError, msg='Flow ID is not provided'):
            check_flow_id()

    def test_check_openai_key(self):
        os.environ['RETRIEVAL_OPENAI_KEY'] = 'sk_mykey'
        key = check_openai_key()
        self.assertEqual(key, 'sk_mykey')

        key = check_openai_key('sk_mynewkey')
        self.assertEqual(key, 'sk_mynewkey')

        os.environ.pop('RETRIEVAL_OPENAI_KEY', None)
        with self.assertRaises(ValueError, msg='No OpenAI key is provided'):
            check_openai_key()


if __name__ == '__main__':
    unittest.main()
