# -*- coding: utf-8 -*-
import streamlit as st
from views.label_view import render_label_tab
from views.summary_report_view import render_summary_report_tab

def show_report_page():
    st.title("🖨️ Report - Nhãn - DSCBCT")

    tab1, tab2 = st.tabs(["🏷️ Nhãn Túi Bài / Túi Đề Thi", "📋 In danh sách CBCT"])

    with tab1:
        render_label_tab()

    with tab2:
        render_summary_report_tab()
