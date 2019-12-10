import pandas as pd
import asyncio
import twint
import os

def load_tweet(keyword, limit):

  result_loc = 'tweets.csv'
  c = twint.Config()
  c.Search = keyword
  c.Limit = limit
  c.Lang = 'id'
  c.Custom["tweet"] = ['date','tweet','username']
  c.Output = result_loc
  c.Store_csv = True

  asyncio.set_event_loop(asyncio.new_event_loop())
  twint.run.Search(c)

  df = pd.read_csv(result_loc)
  os.remove(result_loc)

  return df
