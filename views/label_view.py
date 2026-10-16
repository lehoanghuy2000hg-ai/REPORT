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

def map_excel_columns_for_labels(df_raw):
    """
    Trích xuất và map chính xác tiêu đề cột từ file Excel Lịch thi UIS gốc:
    - KHÓA -> Khóa học
    - GIỜ THI -> Giờ BĐ
    - HÌNH THỨC THI -> HT Thi
    - MÔN THI -> Tên HP
    - MÃ LỚP HỌC PHẦN -> Cột C (Lớp HP)
    - LỚP/NGÀNH -> Cột K (Lớp SV), nếu trống lấy Ngành học
    - SỐ LƯỢNG ĐỀ THI -> #SV dự thi / #SV Thi
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    processed_rows = []
    for _, row in df.iterrows():
        # 1. Khóa
        khoa = str(row.get("Khóa học", row.get("Khóa", ""))).strip()
        if khoa.lower() in ["nan", "none"]: khoa = ""

        # 2. Hệ / Bậc
        he_bac = str(row.get("Bậc ĐT", row.get("Hệ/Bậc", "Đại học (KSV)"))).strip()
        if he_bac.lower() in ["nan", "none"] or not he_bac: he_bac = "Đại học (KSV)"

        # 3. Ngày thi
        ngay_raw = str(row.get("Ngày thi", row.get("Ngày KT", ""))).strip()
        ngay_clean = ngay_raw.split(" ")[0].replace("00:00:00", "").strip()
        match_ngay = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', ngay_clean)
        if match_ngay:
            ngay_thi = f"{match_ngay.group(3)}/{match_ngay.group(2)}/{match_ngay.group(1)}"
        else:
            ngay_thi = ngay_clean if ngay_clean.lower() not in ["nan", "none"] else ""

        # 4. Giờ thi (Giờ BĐ)
        gio_raw = str(row.get("Giờ BĐ", row.get("Giờ thi", ""))).strip()
        gio_thi = gio_raw if gio_raw.lower() not in ["nan", "none"] else ""

        # 5. Phòng thi
        phong_raw = str(row.get("Phòng thi", "")).strip()
        phong_thi = phong_raw if phong_raw.lower() not in ["nan", "none"] else ""

        # 6. Hình thức thi
        ht_raw = str(row.get("HT Thi", row.get("Hình thức thi", ""))).strip()
        if ht_raw.lower() in ["nan", "none"]:
            ht_raw = "Tự luận tập trung"
        hinh_thuc = re.sub(r'\s*\(\d+\)$', '', ht_raw).strip()

        # 7. Môn thi (Tên HP)
        mon_thi = str(row.get("Tên HP", row.get("Môn thi", row.get("Tên học phần", "")))).strip()
        if mon_thi.lower() in ["nan", "none"]: mon_thi = ""

        # 8. Mã lớp học phần (Cột C: Lớp HP)
        ma_lop_hp = str(row.get("Lớp HP", row.get("Mã lớp HP", ""))).strip()
        if ma_lop_hp.lower() in ["nan", "none"]: ma_lop_hp = ""

        # 9. Lớp/Ngành -> Dữ liệu từ cột K (Lớp SV)
        lop_sv = str(row.get("Lớp SV", "")).strip()
        if lop_sv and lop_sv.lower() not in ["nan", "none"]:
            lop_nganh = lop_sv
        else:
            nganh = str(row.get("Ngành học", "")).strip()
            if nganh and nganh.lower() not in ["nan", "none"]:
                lop_nganh = nganh
            else:
                lop_nganh = ma_lop_hp
        if lop_nganh.lower() in ["nan", "none"]: lop_nganh = ""

        # 10. Sĩ số / Số lượng đề thi
        sl_raw = str(row.get("#SV dự thi", row.get("#SV Thi", row.get("SLSV", "")))).strip().replace(".0", "")
        if sl_raw.isdigit():
            slsv = sl_raw
        else:
            slsv = ""

        processed_rows.append({
            "Khóa": khoa,
            "Hệ/Bậc": he_bac,
            "Ngày thi": ngay_thi,
            "Giờ thi": gio_thi,
            "Phòng thi": phong_thi,
            "Hình thức thi": hinh_thuc,
            "Lớp/Ngành": lop_nganh,
            "Môn thi": mon_thi,
            "Mã lớp học phần": ma_lop_hp,
            "SLSV": slsv
        })

    return pd.DataFrame(processed_rows)

def generate_pdf_html(rows_list, report_type="tui_bai"):
    """Tạo HTML/CSS chuẩn khổ A4 kèm nút bấm In trực tiếp góc trên"""
    is_tui_bai = (report_type == "tui_bai")
    
    labels_html = ""
    for idx, row in enumerate(rows_list, start=1):
        khoa = str(row.get("Khóa", ""))
        he_bac = str(row.get("Hệ/Bậc", "Đại học (KSV)"))
        ngay_thi = str(row.get("Ngày thi", ""))
        phong_thi = str(row.get("Phòng thi", ""))
        gio_thi = str(row.get("Giờ thi", ""))
        hinh_thuc = str(row.get("Hình thức thi", ""))
        lop_nganh = str(row.get("Lớp/Ngành", ""))
        mon_thi = str(row.get("Môn thi", ""))
        ma_lop_hp = str(row.get("Mã lớp học phần", ""))
        slsv = str(row.get("SLSV", ""))

        if is_tui_bai:
            # ---------------- MẪU TÚI ĐỰNG BÀI THI ----------------
            title_text = "TÚI ĐỰNG BÀI THI THI KẾT THÚC HỌC PHẦN - LẦN 1"
            box_content = f"""
            <div class="box-border" style="margin-top: 8px;">
                <div class="row-flex">
                    <div class="col"><span class="lbl">SỐ BÀI:</span> ..........</div>
                    <div class="col"><span class="lbl">GHÉP =</span> ........ BÀI</div>
                </div>
                <div class="row-flex" style="margin-top: 6px;">
                    <div class="col"><span class="lbl">SỐ TỜ:</span> ..........</div>
                    <div class="col"><span class="lbl">GHÉP =</span> ........ TỜ</div>
                </div>
            </div>
            """
            header_and_info = f"""
            <div class="row-flex" style="margin-top: 10px;">
                <div class="col"><span class="lbl">KHÓA:</span> {khoa}</div>
                <div class="col"><span class="lbl">HỆ/BẬC:</span> {he_bac}</div>
            </div>

            <div class="row-flex">
                <div class="col"><span class="lbl">NGÀY THI:</span> {ngay_thi}</div>
                <div class="col"><span class="lbl">PHÒNG THI:</span> {phong_thi}</div>
            </div>

            <div class="row-flex">
                <div class="col"><span class="lbl">GIỜ THI:</span> {gio_thi}</div>
                <div class="col"><span class="lbl">HÌNH THỨC THI:</span> {hinh_thuc}</div>
            </div>

            {box_content}

            <div class="field-item" style="margin-top: 10px;">
                <span class="lbl">LỚP/NGÀNH:</span> {lop_nganh}
            </div>

            <div class="field-item" style="margin-top: 8px;">
                <span class="lbl">TÊN HỌC PHẦN:</span> <span style="text-transform: uppercase;"><b>{mon_thi}</b></span>
            </div>

            <div class="field-item" style="margin-top: 6px;">
                <span class="lbl">MÃ LỚP HỌC PHẦN:</span> {ma_lop_hp}
            </div>
            """
            footer_content = """
            <div class="footer-note" style="margin-top: 10px;">
                <div style="font-size: 13pt; font-weight: bold; margin-bottom: 4px;">
                    Hạn cuối nộp bảng điểm về Phòng đào tạo UEH Mekong:
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <div style="font-size: 12.5pt; font-style: italic;">
                        Nộp Bảng điểm cho Phòng đào tạo UEH Mekong đúng hạn
                    </div>
                    <div style="font-size: 13pt; font-weight: bold; white-space: nowrap;">
                        Thư ký nhận bài: ....................
                    </div>
                </div>
            </div>
            """
        else:
            # ---------------- MẪU TÚI ĐỰNG ĐỀ THI ----------------
            title_text = "TÚI ĐỰNG ĐỀ THI THI KẾT THÚC HỌC PHẦN - LẦN 1"
            box_content = f"""
            <div class="box-border" style="margin-top: 10px;">
                <div style="font-size: 14pt; font-weight: bold; margin-bottom: 8px;">
                    SỐ LƯỢNG ĐỀ THI: &nbsp;&nbsp;{slsv if slsv else "........"}
                </div>
                <div class="row-flex" style="font-size: 14pt;">
                    <div><span class="lbl">SL đề phát ra:</span> ___________________</div>
                    <div><span class="lbl">SL đề thu vào:</span> ___________________</div>
                </div>
            </div>
            """
            header_and_info = f"""
            <div class="row-flex" style="margin-top: 10px;">
                <div class="col"><span class="lbl">KHÓA:</span> {khoa}</div>
                <div class="col"><span class="lbl">HỆ/BẬC:</span> {he_bac}</div>
            </div>

            <div style="text-align: center; margin: 6px 0; font-size: 13.5pt;">
                Cơ sở thi: Phân hiệu Đại học Kinh tế TP.HCM tại Tỉnh Vĩnh Long
            </div>

            <div class="field-item" style="margin-top: 6px;">
                <span class="lbl">MÔN THI:</span> <span style="text-transform: uppercase;"><b>{mon_thi}</b></span>
            </div>

            <div class="field-item" style="margin-top: 6px;">
                <span class="lbl">MÃ LỚP HỌC PHẦN:</span> {ma_lop_hp}
            </div>

            <div class="field-item" style="margin-top: 6px;">
                <span class="lbl">LỚP/NGÀNH:</span> {lop_nganh}
            </div>

            <div class="row-flex" style="margin-top: 6px;">
                <div class="col"><span class="lbl">NGÀY THI:</span> {ngay_thi} {f'({gio_thi})' if gio_thi else ''}</div>
                <div class="col"><span class="lbl">PHÒNG THI:</span> {phong_thi}</div>
            </div>

            {box_content}
            """
            footer_content = """
            <div class="footer-note" style="margin-top: 12px; text-align: center;">
                <p style="margin: 4px 0; font-style: italic; font-size: 13.5pt;">
                    <b><u>LƯU Ý:</u></b> Cán bộ coi thi bảo quản đề thi thừa và giao lại cho thư ký vào cuối buổi thi
                </p>
            </div>
            """

        single_label = f"""
        <div class="label-box">
            <div class="index-badge">{idx}</div>
            <div class="header-title">{title_text}</div>
            {header_and_info}
            {footer_content}
        </div>
        """
        labels_html += single_label

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4 portrait;
                margin: 8mm;
            }}
            @media print {{
                .no-print {{ display: none !important; }}
                body {{ background: none; padding: 0; margin: 0; }}
                .label-box {{ 
                    page-break-inside: avoid !important;
                    border: 1.5px solid #000 !important;
                }}
            }}
            body {{
                font-family: 'Times New Roman', Times, serif;
                background-color: #ffffff;
                margin: 0;
                padding: 10px;
                font-weight: normal;
                font-size: 14pt;
            }}
            .label-box {{
                position: relative;
                background: #ffffff;
                width: 100%;
                max-width: 190mm;
                margin: 0 auto 12px auto;
                padding: 6mm 8mm;
                border: 1.5px solid #000;
                box-sizing: border-box;
                page-break-inside: avoid;
            }}
            .index-badge {{
                position: absolute;
                top: 4px;
                left: 6px;
                font-size: 13pt;
                font-weight: bold;
                color: #000;
            }}
            .header-title {{
                text-align: center;
                font-size: 15pt;
                font-weight: bold;
                text-transform: uppercase;
                border-bottom: 2px solid #000;
                padding-bottom: 6px;
            }}
            .lbl {{
                font-weight: bold;
            }}
            .row-flex {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 4px;
                font-size: 13.5pt;
            }}
            .col {{
                flex: 1;
            }}
            .box-border {{
                border: 1.5px solid #000;
                padding: 8px 12px;
            }}
            .field-item {{
                font-size: 14pt;
            }}
            .footer-note {{
                font-size: 12.5pt;
            }}
            .btn-print {{
                background-color: #28a745;
                color: white;
                padding: 10px 22px;
                border: none;
                border-radius: 5px;
                font-size: 15px;
                font-weight: bold;
                cursor: pointer;
                margin-bottom: 15px;
            }}
            .btn-print:hover {{
                background-color: #218838;
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center;">
            <button class="btn-print" onclick="window.print()">🖨️ IN NHÃN</button>
        </div>
        {labels_html}
    </body>
    </html>
    """
    return full_html

def render_label_tab():
    st.subheader("1. Tải tệp dữ liệu làm Nhãn bìa thi")
    uploaded_file = st.file_uploader("📂 Tải tệp Lịch thi / Phân công (.xlsx, .xls)", type=["xlsx", "xls"], key="uploader_label_tab")
    
    if uploaded_file is not None:
        try:
            ext = uploaded_file.name.split(".")[-1].lower()
            df_raw = pd.read_excel(uploaded_file, engine="xlrd" if ext == "xls" else "openpyxl")
            
            df_sessions = map_excel_columns_for_labels(df_raw)

            st.markdown("---")
            st.subheader("2. Danh sách Ca thi / Phòng thi (Tích chọn để xuất nhãn)")
            
            if "select_all_labels" not in st.session_state:
                st.session_state["select_all_labels"] = False

            col_btn1, col_btn2, _ = st.columns([1.5, 1.5, 5])
            with col_btn1:
                if st.button("✅ Chọn tất cả", key="btn_select_all_labels", use_container_width=True):
                    st.session_state["select_all_labels"] = True
                    st.rerun()
            with col_btn2:
                if st.button("❌ Hủy chọn tất cả", key="btn_deselect_all_labels", use_container_width=True):
                    st.session_state["select_all_labels"] = False
                    st.rerun()

            df_sessions.insert(0, "Chọn in", st.session_state["select_all_labels"])

            edited_df = st.data_editor(
                df_sessions,
                column_config={
                    "Chọn in": st.column_config.CheckboxColumn("Chọn in", default=False)
                },
                disabled=[col for col in df_sessions.columns if col != "Chọn in"],
                hide_index=True,
                use_container_width=True,
                key="editor_label_tab"
            )

            selected_rows = edited_df[edited_df["Chọn in"] == True]

            st.markdown("---")
            st.subheader("3. Xem trước 🖨️ & Tải file PDF nhãn về máy")
            
            if selected_rows.empty:
                st.info("💡 Vui lòng tích chọn ít nhất 1 ca thi ở bảng trên để xem trước và xuất nhãn.")
            else:
                st.success(f"✅ Đã chọn **{len(selected_rows)}** ca thi để xuất nhãn bìa.")
                
                report_type = st.radio("Chọn loại nhãn bìa cần xuất:", options=["Túi bài thi", "Túi đề thi"], horizontal=True, key="radio_type_label_tab")
                type_key = "tui_bai" if report_type == "Túi bài thi" else "tui_de"

                rows_list = selected_rows.to_dict(orient="records")
                html_content = generate_pdf_html(rows_list, report_type=type_key)

                pdf_filename = "Nhan_Bia_Tui_Bai_Thi_A4.pdf" if type_key == "tui_bai" else "Nhan_Bia_Tui_De_Thi_A4.pdf"

                if WEASYPRINT_AVAILABLE:
                    try:
                        pdf_bytes = HTML(string=html_content).write_pdf()
                        st.download_button(
                            label=f"📥 TẢI FILE PDF TRỰC TIẾP (.PDF) - {'TÚI BÀI THI' if type_key == 'tui_bai' else 'TÚI ĐỀ THI'}",
                            data=pdf_bytes,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary",
                            key="btn_pdf_label_tab"
                        )
                    except Exception:
                        st.download_button(
                            label="💾 TẢI FILE MẪU IN A4 (.HTML)",
                            data=html_content,
                            file_name=pdf_filename.replace(".pdf", ".html"),
                            mime="text/html",
                            use_container_width=True,
                            type="primary",
                            key="btn_html_fallback_label_tab"
                        )
                else:
                    st.download_button(
                        label="💾 TẢI FILE MẪU IN BÌA A4 (.HTML)",
                        data=html_content,
                        file_name=pdf_filename.replace(".pdf", ".html"),
                        mime="text/html",
                        use_container_width=True,
                        type="primary",
                        key="btn_html_label_tab"
                    )

                components.html(html_content, height=800, scrolling=True)

        except Exception as e:
            st.error(f"❌ Xảy ra lỗi khi xử lý dữ liệu: {e}")
