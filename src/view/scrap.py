import streamlit as st
from lib.Twint import load_tweet
from tokenizer import tokenize, TOK
import re
from bs4 import BeautifulSoup
import pandas as pd
import lxml
import nltk
from nltk.tokenize import WordPunctTokenizer
from textblob import TextBlob
import io
import lib.MongoPanda as mp
import matplotlib.pyplot as plt
from PIL import Image


def scraps():
  image = Image.open('background.jpg')
  st.image(image,use_column_width=True)
  st.title('Scraping Twitter')
  keyword = st.text_input('Input Keyword for Screep')
  limit = st.number_input('Input Limit for Screep', 20, step=20)
  tweet_data = None 
  df = None

  insert = st.checkbox('Insert to Database')

  if st.button("Start"):
    if keyword != "" and limit != "":
      st.text("Keyword : "+keyword)
      st.text("Limit : "+str(limit))
      st.subheader("Raw data")  
      data_tweet = st.text('Loading data...')
      df = load_tweet(keyword,limit)
      data_tweet.text('Loading data... done!')
      st.table(df['tweet'].head(3))
      st.write(df)

    if keyword != "" and limit != "":
      st.subheader("Remove not required characters")
      removing_data = st.text('Removing not required characters...')
      df['tweet'] = df['tweet'].apply(lambda text: tweet_cleaner(text))
      removing_data.text('Removing... done!')
      st.table(df['tweet'].head(3))
      st.write(df)

    if keyword != "" and limit != "":
      st.subheader("Text Normalizer")
      normalize_data = st.text('Normalizing data...')
      df["tweet"] = df["tweet"].apply(lambda x: word_normalize(x))
      normalize_data.text('Normalizing... done!')
      st.table(df['tweet'].head(3))
      st.write(df)

    if keyword != "" and limit != "":
      st.subheader("Labeling Data")
      labeling_data = st.text('Labeling data...')
      df["sentiment"] = df["tweet"].apply(lambda x: sentimenLabeling(x))
      labeling_data.text('Labeling... done!')
      st.table(df['tweet'].head(3))
      st.write(df)
    
    if keyword != "" and limit != "":
      st.subheader("Add Keyword Colomn")
      df["keyword"] = keyword
      st.table(df['tweet'].head(3))
      st.write(df)
    
    if insert:
      st.subheader("Inserting to Database")
      client = mp.client()
      mydict = { "keyword": keyword, "num": limit }
      counter1 = client.insert('keywords', mydict)
      counter2 = client.insertmany('tweets',df)
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
  combined_pat = r'|'.join((pat1, pat2, pat3))
  soup = BeautifulSoup(text, 'lxml')
  souped = soup.get_text()
  stripped = re.sub(combined_pat, '', souped)
  try:
    clean = stripped.decode("utf-8-sig").replace(u"\ufffd", "?")
  except:
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
  text = " ".join(word if word not in norm_dic else norm_dic[word] for word in text_tokenized)
  return text

def sentimenLabeling(text):
  analyticts  = TextBlob(text)
  an = analyticts
  
  try:
    if an.detect_language() != 'en':
      an = analyticts.translate(from_lang='id', to='en')
      print(an)
  except:
    print("Skip")
  
  if an.sentiment.polarity > 0:
    return 1
  elif an.sentiment.polarity == 0:
    return 0
  else:
    return -1
  