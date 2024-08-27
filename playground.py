import streamlit as st
import pandas as pd
import numpy as np

st.title('Mohits Web Application')

file = st.file_uploader("Pick a file")

number = st.slider("Pick a number", 0, 100)


date = st.date_input("Pick a date")

st.title('Selected date is ' + str(date))

st.title('Selected number is ' + str(number))
