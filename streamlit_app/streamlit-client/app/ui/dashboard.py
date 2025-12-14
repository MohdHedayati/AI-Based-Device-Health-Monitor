from app.api.client import health_check
import streamlit as st

def render():
    st.title("System Health Monitor")

    if st.button("Check Backend Health"):
        try:
            data = health_check()
            st.success(data)
        except Exception as e:
            st.error(str(e))
