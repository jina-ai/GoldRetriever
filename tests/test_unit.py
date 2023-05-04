import pytest
import os
from src.retriever import check_bearer_token, check_flow_id, check_openai_key


def test_check_bearer_token():
    os.environ['RETRIEVAL_BEARER_TOKEN'] = 'my_bearer_token'

    bearer_token = check_bearer_token()
    assert bearer_token == 'my_bearer_token'

    bearer_token = check_bearer_token(bearer_token='my_new_bearer_token')
    assert bearer_token == 'my_new_bearer_token'

    os.environ.pop('RETRIEVAL_BEARER_TOKEN')
    bearer_token = check_bearer_token(generate=True)
    assert bearer_token

    os.environ.pop('RETRIEVAL_BEARER_TOKEN')
    with pytest.raises(ValueError, match='No Bearer token is provided'):
        check_bearer_token()


def test_check_flow_id():
    os.environ['RETRIEVAL_FLOW_ID'] = 'abcdefghijk'
    flow_id = check_flow_id()
    assert flow_id == 'retrieval-plugin-abcdefghijk'

    flow_id = check_flow_id('new_id')
    assert flow_id == 'retrieval-plugin-new_id'

    flow_id = check_flow_id('retrieval-plugin-123445667')
    assert flow_id == 'retrieval-plugin-123445667'

    os.environ.pop('RETRIEVAL_FLOW_ID')
    with pytest.raises(ValueError, match='Flow ID is not provided'):
        check_flow_id()


def test_check_openai_key():
    os.environ['RETRIEVAL_OPENAI_KEY'] = 'sk_mykey'
    key = check_openai_key()
    assert key == 'sk_mykey'

    key = check_openai_key('sk_mynewkey')
    assert key == 'sk_mynewkey'

    os.environ.pop('RETRIEVAL_OPENAI_KEY')
    with pytest.raises(ValueError, match='No OpenAI key is provided'):
        check_openai_key()
