import streamlit as st
from time import sleep
from navigation import make_sidebar

make_sidebar()

st.title("Welcome to Clean Assistants")

st.write("Please log in to continue")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Log in", type="primary"):
    if username == "Claude1" and password == "Claude2":
        st.session_state.logged_in = True
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("pages/Main.py")
    else:
        st.error("Incorrect username or password")
