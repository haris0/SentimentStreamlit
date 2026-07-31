import streamlit as st

from view.scrap import scraps
from view.sentiment import sentiment


def main():
  st.sidebar.title("App Mode")
  app_mode = st.sidebar.selectbox("Choose the app mode",
    ["Scrape Tweets", "Sentiment Result"])
  if app_mode == "Scrape Tweets":
    scraps()
  elif app_mode == "Sentiment Result":
    sentiment()


if __name__ == "__main__":
  main()
