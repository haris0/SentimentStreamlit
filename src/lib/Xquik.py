import json
import os

API_URL = 'https://xquik.com/api/v1/x/tweets/search'
API_CONTRACT = '2026-04-29'
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 30


class XquikError(Exception):
  pass


def _default_request_get(
  url,
  params,
  headers,
  allow_redirects,
  stream,
  timeout,
):
  import requests

  try:
    return requests.get(
      url,
      params=params,
      headers=headers,
      allow_redirects=allow_redirects,
      stream=stream,
      timeout=timeout,
    )
  except requests.RequestException:
    raise XquikError(
      'Xquik request failed. Check the connection and retry.',
    ) from None


def _read_json_response(response):
  content_length = response.headers.get('Content-Length')
  if content_length is not None:
    try:
      if int(content_length) > MAX_RESPONSE_BYTES:
        raise XquikError('Xquik response is too large. Reduce the result limit.')
    except ValueError:
      pass

  chunks = []
  total_bytes = 0
  for chunk in response.iter_content(chunk_size=65536):
    if not chunk:
      continue

    total_bytes += len(chunk)
    if total_bytes > MAX_RESPONSE_BYTES:
      raise XquikError('Xquik response is too large. Reduce the result limit.')
    chunks.append(chunk)

  try:
    return json.loads(b''.join(chunks).decode('utf-8'))
  except (UnicodeDecodeError, ValueError):
    raise XquikError(
      'Xquik returned an invalid response. Retry the search.',
    ) from None


def _normalize_tweets(payload, limit):
  if not isinstance(payload, dict) or not isinstance(payload.get('tweets'), list):
    raise XquikError('Xquik returned an invalid response. Retry the search.')

  normalized = []
  for tweet in payload['tweets'][:limit]:
    if not isinstance(tweet, dict) or not isinstance(tweet.get('text'), str):
      continue

    author = tweet.get('author')
    if not isinstance(author, dict):
      author = {}

    date = tweet.get('created_at') or tweet.get('createdAt')
    if not isinstance(date, str):
      date = ''

    username = author.get('username')
    if not isinstance(username, str):
      username = ''

    normalized.append({
      'date': date,
      'tweet': tweet['text'],
      'username': username,
    })

  return normalized


def search_tweets(query, limit, api_key=None, request_get=None):
  if not isinstance(query, str) or query.strip() == '':
    raise XquikError('Search query is required. Enter a keyword first.')
  if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
    raise XquikError('Result limit must be between 1 and 200.')

  credential = api_key or os.environ.get('XQUIK_API_KEY')
  if not isinstance(credential, str) or credential.strip() == '':
    raise XquikError('Xquik API key is missing. Set XQUIK_API_KEY first.')

  requester = request_get or _default_request_get
  response = requester(
    API_URL,
    params={'q': query.strip(), 'language': 'id', 'limit': limit},
    headers={
      'Accept': 'application/json',
      'x-api-key': credential.strip(),
      'xquik-api-contract': API_CONTRACT,
    },
    allow_redirects=False,
    stream=True,
    timeout=REQUEST_TIMEOUT_SECONDS,
  )

  try:
    if response.status_code == 401:
      raise XquikError('Xquik API key is invalid. Create a new key and retry.')
    if response.status_code == 402:
      raise XquikError('Xquik credits are required. Add credits and retry.')
    if response.status_code == 429:
      raise XquikError('Xquik rate limit reached. Wait, then retry.')
    if response.status_code != 200:
      raise XquikError('Xquik search failed. Retry the search.')

    return _normalize_tweets(_read_json_response(response), limit)
  finally:
    response.close()


def load_tweet(query, limit, api_key=None, request_get=None):
  import pandas as pd

  return pd.DataFrame(
    search_tweets(query, limit, api_key=api_key, request_get=request_get),
    columns=['date', 'tweet', 'username'],
  )
