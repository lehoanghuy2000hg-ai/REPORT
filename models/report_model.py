# -*- coding: utf-8 -*-
import pandas as pd

class ReportModel:
    @staticmethod
    def extract_exam_sessions(df):
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        # Tìm các cột tương ứng theo yêu cầu
        col_ma_ca = "Mã ca thi" if "Mã ca thi" in df.columns else df.columns[0]
        col_ma_lop = "Mã lớp HP" if "Mã lớp HP" in df.columns else df.columns[1]
        col_ten_hp = "Tên học phần" if "Tên học phần" in df.columns else df.columns[2]
        col_ngay_thi = "Ngày thi" if "Ngày thi" in df.columns else (df.columns[6] if len(df.columns) > 6 else None)
        col_gio_thi = "Giờ thi" if "Giờ thi" in df.columns else (df.columns[7] if len(df.columns) > 7 else None)
        col_phong_thi = "Phòng thi" if "Phòng thi" in df.columns else (df.columns[8] if len(df.columns) > 8 else None)
        col_slsv = "SLSV" if "SLSV" in df.columns else (df.columns[9] if len(df.columns) > 9 else None)
        col_cbct = "Phân công CBCT" if "Phân công CBCT" in df.columns else (df.columns[10] if len(df.columns) > 10 else None)
        col_hinh_thuc = "Hình thức thi" if "Hình thức thi" in df.columns else (df.columns[12] if len(df.columns) > 12 else None)
        col_co_so_hoc = "Cơ sở học" if "Cơ sở học" in df.columns else (df.columns[24] if len(df.columns) > 24 else "Phân hiệu Vĩnh Long")

        sessions = []
        for _, row in df.iterrows():
            ma_ca = row.get(col_ma_ca, "")
            if pd.isna(ma_ca) or str(ma_ca).strip() == "":
                continue

            ma_lop = str(row.get(col_ma_lop, ""))
            ten_hp = str(row.get(col_ten_hp, ""))
            ngay_thi = str(row.get(col_ngay_thi, ""))
            gio_thi = str(row.get(col_gio_thi, ""))
            phong_thi = str(row.get(col_phong_thi, ""))
            slsv = row.get(col_slsv, "")
            
            # Tách danh sách CBCT và chuẩn hóa ngắt dòng trong ô
            raw_cbct = str(row.get(col_cbct, ""))
            if raw_cbct.lower() in ["nan", "none", "null", ""]:
                cbct_formatted = ""
            else:
                people = [p.strip() for p in raw_cbct.replace("\n", ",").replace(";", ",").split(",") if p.strip()]
                cbct_formatted = "\n".join(people)

            hinh_thuc = str(row.get(col_hinh_thuc, ""))
            co_so_hoc = str(row.get(col_co_so_hoc, ""))

            sessions.append({
                "Mã ca thi": ma_ca,
                "Mã lớp HP": ma_lop,
                "Tên học phần": ten_hp,
                "Ngày thi": ngay_thi,
                "Giờ thi": gio_thi,
                "Phòng thi": phong_thi,
                "SLSV": slsv,
                "Phân công CBCT": cbct_formatted,
                "Hình thức thi": hinh_thuc,
                "Cơ sở học": co_so_hoc,
                "Số bài": "",
                "Số tờ": ""
            })

        return pd.DataFrame(sessions)
