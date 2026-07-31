import re

import nltk
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from nltk.tokenize import WordPunctTokenizer
from PIL import Image
from textblob import TextBlob
from textblob.exceptions import NotTranslated, TranslatorError

import lib.MongoPanda as mp
from lib.Twint import load_tweet as load_twint_tweets
from lib.Xquik import XquikError
from lib.Xquik import load_tweet as load_xquik_tweets


def scraps():
  image = Image.open('background.jpg')
  st.image(image,use_column_width=True)
  st.title('Scraping Tweets')
  source = st.radio('Tweet Source', ['Twint', 'Xquik'])
  keyword = st.text_input('Input Keyword')
  limit = st.number_input(
    'Input Limit',
    min_value=1,
    max_value=200,
    value=20,
    step=20,
  )
  insert = st.checkbox('Insert to Database')

  if st.button("Start"):
    if keyword == "":
      st.warning('Input a keyword first')
      return

    st.text("Source: "+source)
    st.text("Keyword: "+keyword)
    st.text("Limit: "+str(limit))
    st.subheader("Raw data")
    data_tweet = st.text('Loading data...')

    try:
      if source == 'Xquik':
        df = load_xquik_tweets(keyword, int(limit))
      else:
        df = load_twint_tweets(keyword, int(limit))
    except XquikError as error:
      st.error(str(error))
      return

    data_tweet.text('Loading data... done!')
    if df.empty:
      st.warning('No tweets found. Change the query and retry.')
      return

    st.table(df['tweet'].head(3))
    st.write(df)

    st.subheader("Remove not required characters")
    removing_data = st.text('Removing not required characters...')
    df['tweet'] = df['tweet'].apply(lambda text: tweet_cleaner(text))
    removing_data.text('Removing... done!')
    st.table(df['tweet'].head(3))
    st.write(df)

    st.subheader("Text Normalizer")
    normalize_data = st.text('Normalizing data...')
    df["tweet"] = df["tweet"].apply(lambda x: word_normalize(x))
    normalize_data.text('Normalizing... done!')
    st.table(df['tweet'].head(3))
    st.write(df)

    st.subheader("Labeling Data")
    labeling_data = st.text('Labeling data...')
    df["sentiment"] = df["tweet"].apply(lambda x: sentimenLabeling(x))
    labeling_data.text('Labeling... done!')
    st.table(df['tweet'].head(3))
    st.write(df)

    st.subheader("Add Keyword Column")
    df["keyword"] = keyword
    st.table(df['tweet'].head(3))
    st.write(df)

    if insert:
      st.subheader("Inserting to Database")
      client = mp.client()
      mydict = { "keyword": keyword, "num": limit }
      client.insert('keywords', mydict)
      client.insertmany('tweets',df)
      st.success('Insert data success')
    
    # To remove a specific field name from all documents
    # client = mp.client()
    # client.update('tweets','date')
    # st.success('Update success')

    # To remove all documents
    # client = mp.client()
    # client.deleteall('tweets')
    # client.deleteall('keywords')

    # To remove documents with category
    # client = mp.client()
    # client.deleteByValue(keyword)
    # st.success('Delete data success')

@st.cache
def tweet_cleaner(text):
  tok = WordPunctTokenizer()
  pat1 = r'@[A-Za-z0-9]+'
  pat2 = r'https?://[A-Za-z0-9./]+'
  pat3 = r'pic.twitter.com/[A-Za-z0-9./]+'
  combined_pat = f'{pat1}|{pat2}|{pat3}'
  soup = BeautifulSoup(text, 'lxml')
  souped = soup.get_text()
  stripped = re.sub(combined_pat, '', souped)
  try:
    clean = stripped.decode("utf-8-sig").replace("\ufffd", "?")
  except AttributeError:
    clean = stripped
  letters_only = re.sub("[^a-zA-Z]", " ", clean)
  lower_case = letters_only.lower()
  words = tok.tokenize(lower_case)
  return (" ".join(words)).strip()

@st.cache
def word_normalize(text):
  norm = pd.read_csv('key_norm.csv')

  norm_dic = pd.Series(norm.hasil.values,index=norm.singkat).to_dict()  
  text_tokenized = nltk.word_tokenize(text.lower())
  text = " ".join(norm_dic.get(word, word) for word in text_tokenized)
  return text

def sentimenLabeling(text):
  analyticts  = TextBlob(text)
  an = analyticts
  
  try:
    if an.detect_language() != 'en':
      an = analyticts.translate(from_lang='id', to='en')
      st.info(str(an))
  except (NotTranslated, TranslatorError):
    an = analyticts
  
  if an.sentiment.polarity > 0:
    return 1
  elif an.sentiment.polarity == 0:
    return 0
  else:
    return -1
