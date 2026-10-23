# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

def process_group_by_date_and_time(df):
    if df is None or df.empty:
        return pd.DataFrame()
        
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    col_ngay = "Ngày thi" if "Ngày thi" in df.columns else (df.columns[26] if len(df.columns) > 26 else None)
    col_gio = "Giờ BĐ" if "Giờ BĐ" in df.columns else ("Giờ thi" if "Giờ thi" in df.columns else None)
    col_coso = "Cơ sở học" if "Cơ sở học" in df.columns else ("CS Thi" if "CS Thi" in df.columns else None)

    if not col_ngay or not col_gio:
        return df

    df["_ngay_str"] = pd.to_datetime(df[col_ngay], errors="coerce").dt.strftime("%d/%m/%Y").fillna(df[col_ngay].astype(str))
    df["_gio_str"] = df[col_gio].astype(str).str.strip()

    grouped_sessions = []
    
    for (ngay, gio), group in df.groupby(["_ngay_str", "_gio_str"]):
        co_so_val = "Phân hiệu Vĩnh Long"
        if col_coso and col_coso in group.columns:
            valid_cs = group[col_coso].dropna().unique()
            if len(valid_cs) > 0:
                co_so_val = str(valid_cs[0])

        rows_data = []
        all_ca = []
        all_phong = []
        for _, row in group.iterrows():
            m_ca = str(row.get("Mã phòng thi", row.get("Mã ca thi", ""))).strip().replace(".0", "")
            m_lop = str(row.get("Lớp HP", row.get("Mã lớp HP", ""))).strip()
            t_hp = str(row.get("Tên HP", row.get("Tên học phần", ""))).strip()
            sl = str(row.get("#SV dự thi", row.get("#SV Thi", row.get("SLSV", "")))).strip().replace(".0", "")
            p_thi = str(row.get("Phòng thi", "")).strip()
            ht = str(row.get("HT Thi", row.get("Hình thức thi", ""))).strip()
            ht = re.sub(r'\s*\(\d+\)$', '', ht).strip()
            cb = str(row.get("Giảng viên", row.get("Phân công CBCT", ""))).strip()

            if m_ca and m_ca not in all_ca and m_ca.lower() != "nan":
                all_ca.append(m_ca)
            if p_thi and p_thi not in all_phong and p_thi.lower() != "nan":
                all_phong.append(p_thi)

            rows_data.append({
                "Mã ca thi": m_ca if m_ca.lower() != "nan" else "",
                "Mã lớp HP": m_lop if m_lop.lower() != "nan" else "",
                "Tên học phần": t_hp if t_hp.lower() != "nan" else "",
                "SLSV": sl if sl.lower() != "nan" else "0",
                "Phòng thi": p_thi if p_thi.lower() != "nan" else "",
                "Hình thức thi": ht if ht.lower() != "nan" else "",
                "Phân công CBCT": cb if cb.lower() not in ["nan", "none", ""] else "Chưa phân công"
            })

        grouped_sessions.append({
            "Ngày thi": ngay,
            "Giờ thi": gio,
            "Cơ sở học": co_so_val,
            "rows_data": rows_data,
            "Mã ca thi": " / ".join(all_ca),
            "Phòng thi": " / ".join(all_phong),
            "Số bài": "",
            "Số tờ": ""
        })

    return pd.DataFrame(grouped_sessions)

def clean_cbct_format_html(val):
    if not val or pd.isna(val): 
        return "Chưa phân công"
    
    parts = [p.strip() for p in str(val).replace('\n', ';').replace(',', ';').split(';') if p.strip()]
    parsed_items = []
    
    for p in parts:
        p_clean = re.sub(r'\s*-\s*0(?=\s*\)|$)', '', p).strip()
        p_lower = p_clean.lower()
        
        priority = 99

        if "cbct1" in p_lower:
            priority = 1
        elif "cbct2" in p_lower:
            priority = 2
        elif "phòng máy" in p_lower or "phong may" in p_lower:
            priority = 3
        elif "lãnh đạo" in p_lower or "lanh dao" in p_lower:
            priority = 4
        elif "thường trực" in p_lower or "thuong truc" in p_lower:
            priority = 5
        elif "tiếp nhận" in p_lower or "tiep nhan" in p_lower:
            priority = 6
        elif "thư ký" in p_lower or "thu ky" in p_lower:
            priority = 7
        elif "giám sát" in p_lower or "giam sat" in p_lower:
            priority = 8
        elif "hỗ trợ kỹ thuật" in p_lower or "ho tro ky thuat" in p_lower:
            priority = 9

        match_bracket = re.match(r'^(.*?)\s*\((.*?)\)\s*$', p_clean)
        if match_bracket:
            name_part = match_bracket.group(1).strip()
            role_part = match_bracket.group(2).strip()
            formatted_text = f"{name_part} - <b>{role_part}</b>"
        elif " - " in p_clean:
            name_part, role_part = p_clean.split(" - ", 1)
            formatted_text = f"{name_part.strip()} - <b>{role_part.strip()}</b>"
        else:
            formatted_text = p_clean

        parsed_items.append((priority, formatted_text))

    parsed_items.sort(key=lambda x: x[0])
    return "<br>".join([item[1] for item in parsed_items])

def generate_custom_report_html(selected_sessions_list):
    reports_body_html = ""
    
    for idx_page, session_info in enumerate(selected_sessions_list, start=1):
        ngay_thi = str(session_info.get("Ngày thi", ""))
        gio_thi = str(session_info.get("Giờ thi", ""))
        co_so_hoc = str(session_info.get("Cơ sở học", "Phân hiệu Vĩnh Long"))
        rows_data = session_info.get("rows_data", [])

        room_groups = []
        for r in rows_data:
            p = r.get("Phòng thi", "")
            if not room_groups or room_groups[-1]["room"] != p:
                room_groups.append({"room": p, "rows": [r]})
            else:
                room_groups[-1]["rows"].append(r)

        table_rows_html = ""
        stt_global = 1
        for group in room_groups:
            r_rows = group["rows"]
            row_span_count = len(r_rows)
            
            cbcts_in_room = [row_item.get("Phân công CBCT", "") for row_item in r_rows if row_item.get("Phân công CBCT", "")]
            best_cbct_room = max(cbcts_in_room, key=len) if cbcts_in_room else "Chưa phân công"
            formatted_cbct = clean_cbct_format_html(best_cbct_room)

            for idx_r, r in enumerate(r_rows):
                cbct_cell_html = ""
                if idx_r == 0:
                    cbct_cell_html = f'<td rowspan="{row_span_count}" style="text-align: left; padding-left: 6px; vertical-align: middle;">{formatted_cbct}</td>'

                table_rows_html += f"""
                <tr>
                    <td style="text-align: center; vertical-align: middle;">{stt_global}</td>
                    <td style="text-align: center; vertical-align: middle;">{r.get('Mã ca thi', '')}</td>
                    <td style="text-align: center; vertical-align: middle;">{r.get('Mã lớp HP', '')}</td>
                    <td style="text-align: left; padding-left: 5px; vertical-align: middle;"><b>{r.get('Tên học phần', '')}</b></td>
                    <td style="text-align: center; vertical-align: middle;">{gio_thi}</td>
                    <td style="text-align: center; vertical-align: middle;">{r.get('Phòng thi', '')}</td>
                    <td style="text-align: center; vertical-align: middle;">{r.get('SLSV', '')}</td>
                    <td style="text-align: center; vertical-align: middle;">{r.get('Hình thức thi', '')}</td>
                    {cbct_cell_html}
                    <td style="text-align: center; vertical-align: middle;"></td>
                    <td style="text-align: center; vertical-align: middle;"></td>
                </tr>
                """
                stt_global += 1

        single_page_html = f"""
        <div class="page-container">
            <table class="header-table">
                <tr>
                    <td style="width: 45%; text-align: center;">
                        <b>TRƯỜNG ĐẠI HỌC KINH TẾ TP.HCM</b><br>
                        <b>PHÂN HIỆU TẠI TỈNH VĨNH LONG</b>
                    </td>
                    <td style="width: 55%; text-align: center;">
                        <b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br>
                        <b><u>Độc lập - Tự do - Hạnh phúc</u></b>
                    </td>
                </tr>
            </table>

            <div class="title-box">
                <div class="main-title">BẢNG TỔNG HỢP PHÂN CÔNG COI THI & ĐIỂM DANH</div>
            </div>

            <div class="info-box">
                <div class="info-row">
                    <span class="lbl">Ngày thi:</span> {ngay_thi} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
                    <span class="lbl">Giờ thi (Ca thi):</span> {gio_thi}
                </div>
                <div class="info-row" style="margin-top: 4px;"><span class="lbl">Cơ sở thi:</span> {co_so_hoc}</div>
            </div>

            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 2.5%;">STT</th>
                        <th style="width: 7.5%;">Mã ca thi</th>
                        <th style="width: 11.5%;">Mã lớp HP</th>
                        <th style="width: 18.5%;">Tên học phần</th>
                        <th style="width: 4.8%;">Giờ thi</th>
                        <th style="width: 6.8%;">Phòng thi</th>
                        <th style="width: 3.4%;">SLSV</th>
                        <th style="width: 14.5%;">Hình thức thi</th>
                        <th style="width: 23.4%;">Phân công CBCT</th>
                        <th style="width: 3.8%;">Số bài</th>
                        <th style="width: 3.8%;">Số tờ</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>

            <div style="margin-top: 25px; text-align: right; font-size: 10pt; font-style: italic;">
                Vĩnh Long, ngày ..... tháng ..... năm 202...<br>
                <b>XÁC NHẬN CỦA PHÒNG ĐÀO TẠO</b>
            </div>
        </div>
        """
        reports_body_html += single_page_html

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ 
                size: A4 landscape; 
                margin: 8mm; 
            }}
            @media print {{
                .no-print {{ display: none !important; }}
                body {{ background: none; padding: 0; margin: 0; }}
                .page-container {{ page-break-after: always !important; border: none !important; margin: 0 !important; padding: 0 !important; }}
                @page {{ margin: 8mm; }}
            }}
            body {{ font-family: 'Times New Roman', Times, serif; font-size: 9.5pt; line-height: 1.2; color: #000; margin: 0; padding: 5px; background-color: #ffffff; }}
            .page-container {{
                background: #ffffff;
                padding: 5px;
                margin-bottom: 15px;
                box-sizing: border-box;
                page-break-after: always;
            }}
            .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
            .header-table td {{ vertical-align: top; font-size: 9.5pt; line-height: 1.15; }}
            .title-box {{ text-align: center; margin: 8px 0 12px 0; }}
            .main-title {{ font-size: 12pt; font-weight: bold; text-transform: uppercase; }}
            .info-box {{ margin-bottom: 10px; font-size: 10pt; }}
            .info-row {{ margin-bottom: 3px; }}
            .lbl {{ font-weight: bold; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
            .data-table th, .data-table td {{ border: 1px solid #000; padding: 3px 3px; font-size: 9pt; }}
            .data-table th {{ text-align: center; font-weight: bold; background-color: #f2f2f2; }}
            .btn-print {{ background-color: #28a745; color: white; padding: 8px 18px; border: none; border-radius: 5px; font-size: 14px; font-weight: bold; cursor: pointer; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center;">
            <button class="btn-print" onclick="window.print()">🖨️ IN TẤT CẢ BÁO CÁO (A4 NGANG)</button>
        </div>
        {reports_body_html}
    </body>
    </html>
    """
    return full_html

def render_summary_report_tab():
    st.subheader("1. Tải tệp dữ liệu xuất Báo cáo Tổng hợp")
    file_tab2 = st.file_uploader("📂 Tải tệp Lịch thi / Phân công coi thi (.xlsx, .xls)", type=["xlsx", "xls"], key="uploader_summary_tab")

    if file_tab2 is not None:
        try:
            ext2 = file_tab2.name.split(".")[-1].lower()
            df_raw2 = pd.read_excel(file_tab2, engine="xlrd" if ext2 == "xls" else "openpyxl")
            
            df_sessions2 = process_group_by_date_and_time(df_raw2)

            st.markdown("---")
            st.subheader("2. Danh sách Ca thi tổng hợp theo Ngày & Giờ (Tích chọn để xuất Báo cáo)")
            
            col_btn1, col_btn2, _ = st.columns([1.5, 1.5, 5])
            with col_btn1:
                if st.button("✅ Chọn tất cả", key="btn_select_all_summary", use_container_width=True):
                    for idx in range(len(df_sessions2)):
                        st.session_state[f"chk_summary_{idx}"] = True
                    st.rerun()
            with col_btn2:
                if st.button("❌ Hủy chọn tất cả", key="btn_deselect_all_summary", use_container_width=True):
                    for idx in range(len(df_sessions2)):
                        st.session_state[f"chk_summary_{idx}"] = False
                    st.rerun()

            selected_rows2 = []
            for idx, row in df_sessions2.iterrows():
                if f"chk_summary_{idx}" not in st.session_state:
                    st.session_state[f"chk_summary_{idx}"] = False

                with st.container(border=True):
                    cols = st.columns([0.5, 2, 1.5, 2, 4])
                    with cols[0]:
                        chk = st.checkbox("Chọn", key=f"chk_summary_{idx}")
                    with cols[1]:
                        st.markdown(f"**Ngày:** {row['Ngày thi']}")
                        st.markdown(f"**Giờ:** {row['Giờ thi']}")
                    with cols[2]:
                        st.markdown(f"**Phòng:** `{row['Phòng thi']}`")
                    with cols[3]:
                        st.markdown(f"**Mã ca:** {row['Mã ca thi']}")
                    with cols[4]:
                        st.markdown(f"**Số lớp:** {len(row['rows_data'])} lớp")
                    
                    if chk:
                        selected_rows2.append(row.to_dict())

            st.markdown("---")
            st.subheader("3. Xem trước 🖨️ & Tải Báo cáo Tổng hợp Hàng loạt A4 Ngang")

            if not selected_rows2:
                st.info("💡 Vui lòng tích chọn ít nhất 1 ca thi ở bảng trên để xem trước và xuất báo cáo.")
            else:
                st.success(f"✅ Đã chọn **{len(selected_rows2)}** ca thi tổng hợp để xuất báo cáo.")

                custom_report_html = generate_custom_report_html(selected_rows2)
                
                if WEASYPRINT_AVAILABLE:
                    pdf_bytes_gv2 = HTML(string=custom_report_html).write_pdf()
                    st.download_button("📥 TẢI FILE PDF TRỰC TIẾP (.PDF)", data=pdf_bytes_gv2, file_name="Bao_Cao_Tong_Hop_Ca_Thi.pdf", mime="application/pdf", use_container_width=True, type="primary", key="btn_pdf_summary_tab")
                else:
                    st.download_button("💾 TẢI FILE MẪU IN (.HTML)", data=custom_report_html, file_name="Bao_Cao_Tong_Hop_Ca_Thi.html", mime="text/html", use_container_width=True, type="primary", key="btn_html_summary_tab")

                components.html(custom_report_html, height=800, scrolling=True)

        except Exception as e:
            st.error(f"❌ Xảy ra lỗi: {e}")
