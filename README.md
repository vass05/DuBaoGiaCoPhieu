# Hệ Thống Dự Báo Giá Cổ Phiếu Bằng Mô Hình Học Sâu RNN (Kiến Trúc MVC)

Ứng dụng web được xây dựng theo mô hình kiến trúc chuẩn **MVC (Model - View - Controller)**, sử dụng mô hình học sâu **Stacked SimpleRNN** đã huấn luyện và lưu tại thư mục `models/` (`rnn_stock_model.keras` và `stock_scaler.pkl`) để dự báo giá đóng cửa cổ phiếu.

---

## 1. Cấu Trúc Kiến Trúc MVC

```
RNN/
│
├── app.py                      # Điểm khởi chạy ứng dụng Flask, liên kết Controller và View
├── config.py                   # Cấu hình hệ thống (tham số cửa sổ trượt 60 ngày, đường dẫn, port)
├── run_app.bat                 # Script chạy ứng dụng nhanh bằng 1 click chuột trên Windows
├── requirements.txt            # Danh sách thư viện phụ thuộc
│
├── models/                     # [TẦNG MODEL] Xử lý dữ liệu & Mô hình AI
│   ├── __init__.py
│   ├── rnn_stock_model.keras   # File mô hình Keras đã huấn luyện
│   ├── stock_scaler.pkl        # File MinMaxScaler đã fit
│   ├── predictor.py            # Lớp StockPredictor: Nạp mô hình, suy luận dự báo, rolling multi-step, tính sai số kiểm thử
│   └── data_loader.py          # Lớp StockDataLoader: Đọc dữ liệu lịch sử CSV, xử lý dữ liệu nhập tùy biến
│
├── controllers/                # [TẦNG CONTROLLER] Điều phối luồng và xử lý yêu cầu
│   ├── __init__.py
│   └── stock_controller.py     # Điều hướng các tuyến đường Web & REST API, xác thực tham số, gọi Model
│
├── views/                      # [TẦNG VIEW] Giao diện người dùng (HTML Templates)
│   ├── base.html               # Khung bố cục chung: Header, Navigation tối giản, Footer
│   ├── index.html              # Bảng điều khiển chính: Chọn mã cổ phiếu, xem biểu đồ và kết quả dự báo
│   ├── evaluate.html           # Màn hình đánh giá: Kiểm thử mô hình trên tập Test (MAE, RMSE, MSE, biểu đồ đối chiếu)
│   └── custom.html             # Màn hình dự báo tùy biến: Nhập 60 số thủ công hoặc tải file CSV
│
└── static/                     # Tài nguyên giao diện tĩnh
    ├── css/
    │   └── style.css           # Bố cục tối giản, gam màu trung tính nhã nhặn (Slate / Deep Blue / Forest Green), không icon màu mè
    └── js/
        ├── chart.umd.min.js    # Thư viện Chart.js cục bộ (hoạt động tốt cả khi offline)
        ├── main.js             # Logic biểu đồ tương tác và cập nhật dữ liệu tự động
        ├── evaluate.js         # Logic vẽ biểu đồ đối chiếu tập Test
        └── custom.js           # Logic xử lý nhập số liệu tùy biến và upload CSV
```

---

## 2. Đặc Điểm Giao Diện & Trải Nghiệm Người Dùng (UI/UX)

- **Phong cách tối giản, nhã nhặn (Minimalist & Clean Financial Theme)**:
  - Sử dụng bảng màu sắc trung tính dịu mắt (`Slate #0f172a`, `Background #f8fafc`, `Card #ffffff`), độ tương phản cao nhưng không gây mỏi mắt khi quan sát dữ liệu tài chính trong thời gian dài.
  - **Tuyệt đối không dùng icon sặc sỡ hay màu mè**: Sử dụng văn bản rõ nghĩa, thẻ chỉ số (badge/tag) đơn sắc tinh tế, đường nét mảnh gãy gọn.
- **Biểu đồ động trực quan**:
  - Dữ liệu lịch sử 60 ngày hiển thị bằng nét liền màu than chì tối giản.
  - Chuỗi dự báo tương lai hiển thị bằng nét đứt xanh dương thanh lịch, có chấm điểm phiên rõ ràng.
- **Chức năng chính**:
  1. **Dự báo thị trường**: Chọn mã cổ phiếu (AAPL mặc định chuẩn, MSFT, GOOGL, AMZN, FB, NVDA, IBM, AAL...) và số ngày dự báo (1, 3, 7, 14, 30 ngày).
  2. **Đánh giá mô hình**: Xem chỉ số MAE, RMSE, MSE và biểu đồ so sánh Giá thực tế vs Giá dự báo trên toàn bộ 192 phiên kiểm thử độc lập.
  3. **Dữ liệu tùy biến**: Cho phép nhập trực tiếp danh sách 60 mức giá (hỗ trợ nút *Điền 60 giá mẫu thực tế*) hoặc kéo thả file CSV bất kỳ để chạy suy luận.

---

## 3. Cách Khởi Động Ứng Dụng

### Cách 1: Sử dụng file chạy nhanh (Khuyên dùng)
Nhấp đúp chuột vào file [run_app.bat](file:///d:/K%C3%AC%201%20N4/Ph%C3%A1t%20tri%E1%BB%83n%20c%C3%A1c%20h%E1%BB%87%20th%E1%BB%91ng%20th%C3%B4ng%20minh/RNN/run_app.bat).

### Cách 2: Chạy qua dòng lệnh Terminal
```powershell
# Chạy trực tiếp bằng môi trường Python đã có TensorFlow và Flask:
& "C:\Users\PC ASUS\miniconda3\envs\cnn_env\python.exe" app.py
```

Sau khi máy chủ khởi động, mở trình duyệt và truy cập:
👉 **`http://127.0.0.1:5000`**
