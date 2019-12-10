import streamlit as st
import numpy
import pandas as pd
from view.scrap import scraps
from view.sentiment import sentiment

def main():
  st.sidebar.title("App Mode")
  app_mode = st.sidebar.selectbox("Choose the app mode",
    ["Screeps Twitter", "Sentiment Result"])
  if app_mode == "Screeps Twitter":
    scraps()
  elif app_mode == "Sentiment Result":
    sentiment()

if __name__ == "__main__":
    main()