import json
import unittest

from lib.Xquik import (
  API_CONTRACT,
  API_URL,
  MAX_RESPONSE_BYTES,
  XquikError,
  load_tweet,
  search_tweets,
)


class FakeResponse:

  def __init__(self, payload=None, status_code=200, headers=None, raw_body=None):
    self.status_code = status_code
    self.headers = headers or {}
    self.closed = False
    if raw_body is not None:
      self.body = raw_body
    else:
      self.body = json.dumps(payload).encode('utf-8')

  def iter_content(self, chunk_size):
    for offset in range(0, len(self.body), chunk_size):
      yield self.body[offset:offset + chunk_size]

  def close(self):
    self.closed = True


class XquikSearchTest(unittest.TestCase):

  def test_search_normalizes_contract_and_secures_request(self):
    calls = []
    responses = []

    def request_get(url, **kwargs):
      calls.append((url, kwargs))
      response = FakeResponse({
        'tweets': [
          {
            'text': 'A result',
            'created_at': '2026-07-31T09:00:00Z',
            'author': {'username': 'example'},
          },
          {'text': 'Fallback fields', 'createdAt': '2026-07-31T09:01:00Z'},
        ],
        'has_more': False,
        'next_cursor': '',
      })
      responses.append(response)
      return response

    result = search_tweets('agents', 2, api_key='xq_test', request_get=request_get)

    self.assertEqual([
      {
        'date': '2026-07-31T09:00:00Z',
        'tweet': 'A result',
        'username': 'example',
      },
      {
        'date': '2026-07-31T09:01:00Z',
        'tweet': 'Fallback fields',
        'username': '',
      },
    ], result)
    self.assertEqual(API_URL, calls[0][0])
    self.assertEqual(
      {'q': 'agents', 'language': 'id', 'limit': 2},
      calls[0][1]['params'],
    )
    self.assertEqual('xq_test', calls[0][1]['headers']['x-api-key'])
    self.assertEqual(API_CONTRACT, calls[0][1]['headers']['xquik-api-contract'])
    self.assertFalse(calls[0][1]['allow_redirects'])
    self.assertTrue(calls[0][1]['stream'])
    self.assertTrue(responses[0].closed)

  def test_missing_key_is_rejected_before_request(self):
    with self.assertRaisesRegex(XquikError, 'API key is missing'):
      search_tweets('agents', 20, api_key=' ')

  def test_load_tweet_returns_app_dataframe_columns(self):
    def request_get(url, **kwargs):
      return FakeResponse({
        'tweets': [{
          'text': 'A result',
          'created_at': '2026-07-31T09:00:00Z',
          'author': {'username': 'example'},
        }],
      })

    frame = load_tweet(
      'agents',
      1,
      api_key='xq_test',
      request_get=request_get,
    )

    self.assertEqual(['date', 'tweet', 'username'], list(frame.columns))
    self.assertEqual('A result', frame.iloc[0]['tweet'])

  def test_invalid_limit_is_rejected(self):
    for limit in (0, 201, True, '20'):
      with self.subTest(limit=limit), self.assertRaisesRegex(
        XquikError,
        'between 1 and 200',
      ):
        search_tweets('agents', limit, api_key='xq_test')

  def test_http_error_does_not_expose_response_body(self):
    def request_get(url, **kwargs):
      return FakeResponse(
        status_code=500,
        raw_body=b'xq_private_value and internal details',
      )

    with self.assertRaises(XquikError) as raised:
      search_tweets('agents', 20, api_key='xq_test', request_get=request_get)

    self.assertNotIn('xq_private_value', str(raised.exception))
    self.assertNotIn('internal details', str(raised.exception))

  def test_oversized_response_is_rejected(self):
    def request_get(url, **kwargs):
      return FakeResponse(
        payload={},
        headers={'Content-Length': str(MAX_RESPONSE_BYTES + 1)},
      )

    with self.assertRaisesRegex(XquikError, 'too large'):
      search_tweets('agents', 20, api_key='xq_test', request_get=request_get)

  def test_invalid_payload_is_rejected(self):
    def request_get(url, **kwargs):
      return FakeResponse({'results': []})

    with self.assertRaisesRegex(XquikError, 'invalid response'):
      search_tweets('agents', 20, api_key='xq_test', request_get=request_get)


if __name__ == '__main__':
  unittest.main()
