# UEH Mekong Exam Report & Label Generator

Hệ thống web hỗ trợ tự động trích xuất, gom nhóm dữ liệu lịch thi UIS và xuất Báo cáo Tổng hợp ca thi / Nhãn bìa túi bài & túi đề thi khổ A4 chuẩn xác.

## Tính năng chính
- Xuất Nhãn Bìa Thi A4: Tự động trích xuất Môn thi, Lớp/Ngành (từ cột K Lớp SV), Giờ thi, Hình thức thi, Sĩ số.
- Báo cáo Tổng hợp Ca thi A4 Ngang: Gom nhóm ca thi theo Ngày & Giờ, hiển thị đầy đủ thông tin phân công coi thi.
- Chọn hàng loạt: Hỗ trợ nút Chọn tất cả / Hủy chọn tất cả tiện lợi.

## Cài đặt cục bộ (Local)
pip install -r requirements.txt
streamlit run app.py
