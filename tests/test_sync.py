import responses
from autoextract.constants import API_ENDPOINT
from autoextract.batching import build_query
from autoextract.sync import request_raw


@responses.activate
def test_sync_request_success():
    responses.add(responses.POST, API_ENDPOINT, json={'success': 'true'})
    query = build_query(urls=['http://example.com'], page_type='article')

    resp = request_raw(query, 'secret_key')
    assert resp == {'success': 'true'}


@responses.activate
def test_sync_request_error():
    responses.add(responses.POST, API_ENDPOINT, json={'error': 'true'}, status=429)
    query = build_query(urls=['http://example.com'], page_type='article')

    try:
        request_raw(query, 'secret_key')
    except Exception as err:
        assert err.response.status_code == 429
        assert 'User-Agent' in err.request.headers
