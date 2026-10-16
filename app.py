# -*- coding: utf-8 -*-
import streamlit as st
from views.report_view import show_report_page

st.set_page_config(
    page_title="In Danh sách report",
    page_icon="🖨️",
    layout="wide"
)

if __name__ == "__main__":
    show_report_page()
