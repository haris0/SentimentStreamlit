import streamlit as st
import lib.MongoPanda as mp
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import nltk
from wordcloud import WordCloud
from PIL import Image
import asyncio


def sentiment():
  image = Image.open('background.jpg')
  st.image(image,use_column_width=True)
  st.title('Sentiment Result')
  client = mp.client()
  allKeyword = client.retrieve()
  listKeyword = list(allKeyword.keyword)
  listKeyword.insert(0, '')
  keyword = st.selectbox("Choose the Topic",listKeyword)
  
  if keyword != '':
    st.subheader("Data of Selected Keyword")
    allTweets = client.retrieveByValue(keyword=keyword)
    st.write(allTweets)

    st.subheader("Sentiment Analysis Percentage")
    # Data to plot
    labels = 'Positive', 'Netral', 'Negative'
    pos = allTweets[allTweets.sentiment == 1].shape[0]
    net = allTweets[allTweets.sentiment == 0].shape[0]
    neg = allTweets[allTweets.sentiment == -1].shape[0]
    sizes = [pos, net, neg]
    colors = ['lightskyblue', 'gold', 'lightcoral']
    explode = (0.1, 0, 0)  # explode 1st slice

    # Plot
    plt.pie(sizes, explode=explode  , labels=labels, colors=colors,
    autopct='%1.1f%%', startangle=140)

    plt.axis('equal')
    st.pyplot()

    with io.open('stopword_list_TALA.txt', encoding="utf-8") as f:
      stoptext = f.read().lower()
    stopword = nltk.word_tokenize(stoptext)

    st.subheader("WordCloud Positive Tweet")
    asyncio.set_event_loop(asyncio.new_event_loop())
    showWordCloud(allTweets, 1, stopword)

    st.subheader("WordCloud Netral Tweet")
    
    asyncio.set_event_loop(asyncio.new_event_loop())
    showWordCloud(allTweets, 0, stopword)

    st.subheader("WordCloud Negative Tweet")
    asyncio.set_event_loop(asyncio.new_event_loop())
    showWordCloud(allTweets, -1, stopword)


def showWordCloud (df,sentiment, stopwords):
  tweets = df[df.sentiment == sentiment]
  string = []
  for t in tweets.tweet:
      string.append(t)
  string = pd.Series(string).str.cat(sep=' ')

  wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(string)
  plt.figure()
  plt.imshow(wordcloud, interpolation="bilinear")
  plt.axis("off")
  st.pyplot()
