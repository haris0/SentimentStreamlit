import asyncio
import os
import tempfile
from contextlib import contextmanager


@contextmanager
def temporary_tweet_csv_path():
  with tempfile.TemporaryDirectory(prefix='sentimentstreamlit-') as directory:
    yield os.path.join(directory, 'tweets.csv')


def load_tweet(keyword, limit):
  import pandas as pd
  import twint

  with temporary_tweet_csv_path() as result_loc:
    c = twint.Config()
    c.Search = keyword
    c.Limit = limit
    c.Lang = 'id'
    c.Custom["tweet"] = ['date', 'tweet', 'username']
    c.Output = result_loc
    c.Store_csv = True

    asyncio.set_event_loop(asyncio.new_event_loop())
    twint.run.Search(c)

    return pd.read_csv(result_loc)
