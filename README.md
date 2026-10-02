# Hệ Thống Dự Báo Giá Cổ Phiếu Bằng Mô Hình Học Sâu RNN (Kiến Trúc MVC)

Ứng dụng web dự báo giá đóng cửa cổ phiếu theo thời gian thực, xây dựng theo mô hình kiến trúc chuẩn **MVC (Model - View - Controller)**, tích hợp mô hình học sâu **Stacked SimpleRNN** đã huấn luyện (`rnn_stock_model.keras` & `stock_scaler.pkl`).

---

## Trải Nghiệm Ứng Dụng Trực Tuyến (Live Demo)

Ứng dụng đã được triển khai trực tiếp trên đám mây Render.com, có thể truy cập 24/7 từ bất kỳ thiết bị nào (máy tính, điện thoại, máy tính bảng):

- **Link Demo Trực Tuyến**: **[https://dubaogiacophieu.onrender.com/](https://dubaogiacophieu.onrender.com/)**

*(Lưu ý: Nếu sau một khoảng thời gian không có người truy cập, máy chủ miễn phí có thể cần khoảng 30 - 45 giây để khởi động lại ở lần mở đầu tiên).*

---

## Cấu Trúc Dự Án Theo Mô Hình MVC

```
RNN/
│
├── app.py                      # [ENTRY POINT] Khởi tạo Flask, liên kết Controller và View
├── config.py                   # [CONFIG] Cấu hình hệ thống (PORT, HOST, Time-steps 60 ngày)
├── render.yaml                 # [DEPLOY] Cấu hình tự động triển khai trên Render.com
├── Procfile                    # [DEPLOY] Lệnh khởi chạy WSGI Gunicorn tối ưu bộ nhớ
├── requirements.txt            # Danh sách các thư viện phụ thuộc
├── .vscode/                    # Cấu hình môi trường Python cho IDE (tự động nhận diện cnn_env)
│
├── models/                     # [MODEL] Tầng xử lý mô hình AI & Dữ liệu
│   ├── __init__.py
│   ├── rnn_stock_model.keras   # File mô hình Keras SimpleRNN đã huấn luyện
│   ├── stock_scaler.pkl        # File MinMaxScaler chuẩn hóa giá
│   ├── predictor.py            # Lớp StockPredictor: Tải mô hình, suy luận dự báo đơn bước & đa bước
│   └── data_loader.py          # Lớp StockDataLoader: Đọc dữ liệu lịch sử CSV, xử lý chuỗi nhập tùy biến
│
├── controllers/                # [CONTROLLER] Tầng điều phối luồng nghiệp vụ
│   ├── __init__.py
│   └── stock_controller.py     # Tiếp nhận request HTTP & REST API, gọi Model và chuyển dữ liệu tới View
│
├── views/                      # [VIEW] Tầng giao diện người dùng (HTML Templates)
│   ├── base.html               # Khung bố cục chung: Header tối giản, thanh điều hướng
│   ├── index.html              # Bảng điều khiển chính: Chọn mã cổ phiếu, xem biểu đồ và kết quả dự báo
│   └── custom.html             # Màn hình dự báo tự do: Nhập 60 mức giá thủ công hoặc tải file CSV
│
├── static/                     # Tài nguyên giao diện tĩnh
│   ├── css/
│   │   └── style.css           # Giao diện tối giản, gam màu trung tính nhã nhặn, không icon màu mè
│   └── js/
│       ├── chart.umd.min.js    # Thư viện biểu đồ Chart.js cục bộ
│       ├── main.js             # Logic biểu đồ tương tác và cập nhật dữ liệu tự động
│       └── custom.js           # Logic xử lý nhập số liệu tùy biến và upload CSV
│
└── DATA/                       # Dữ liệu tài chính
    └── Stock_Market_Data/
        └── all_stocks_5yr.csv  # Dữ liệu 5 năm lịch sử của hơn 500 mã cổ phiếu S&P 500
```

---

## Các Chức Năng Chính

### 1. Dự Báo Thị Trường (Bảng Điều Khiển Chính)
- **Hỗ trợ 2 nguồn dữ liệu linh hoạt**:
  - ⚡ **Thời gian thực (Real-time Live)**: Tích hợp trực tiếp với **Yahoo Finance**, tự động tải 60 phiên giao dịch mới nhất tính đến thời điểm hiện tại của thị trường chứng khoán Mỹ.
  - 📂 **Dữ liệu mẫu lịch sử (Offline CSV)**: Dữ liệu 5 năm (2013 - 2018) từ tập tin cục bộ.
- **Tra cứu mã cổ phiếu không giới hạn**: Hỗ trợ xem các mã nổi bật (`AAPL`, `MSFT`, `NVDA`, `TSLA`, `GOOGL`, `AMZN`, `META`, `IBM`, `INTC`, `JPM`) hoặc gõ trực tiếp bất kỳ mã cổ phiếu nào theo nhu cầu.
- **Độ dài dự báo linh hoạt**: Chọn dự báo 1 ngày tới ($T+1$), 3 ngày, 7 ngày (1 tuần), 14 ngày (2 tuần) hoặc 30 ngày (1 tháng).
- **Thẻ chỉ số thông minh**: Cập nhật giá đóng cửa gần nhất, giá dự báo phiên tiếp theo, mức chênh lệch USD, tỷ lệ biến động (%) và xu hướng dự kiến (*Tăng / Giảm*).
- **Cơ chế Dynamic Scaling**: Tự động chuẩn hóa dải giá thời gian thực về không gian thích ứng phù hợp cho mạng nơ-ron RNN suy luận mượt mà.
- **Biểu đồ trực quan**: Vẽ kết hợp giữa 60 phiên thực tế trong quá khứ (đường nét liền) và chuỗi dự báo tương lai (đường nét đứt).
- **Bảng thống kê chi tiết**: Liệt kê số liệu từng phiên giao dịch trong tương lai và 10 phiên giao dịch gần nhất.

### 2. Dự Báo Với Dữ Liệu Tùy Biến
- **Nhập chuỗi giá trực tiếp**: Cho phép người dùng nhập hoặc dán dãy tối thiểu 60 mức giá bất kỳ để mô hình phân tích xu hướng.
- **Nút điền mẫu tiện lợi**: Bấm 1-click để tự động nạp 60 giá thực tế mới nhất để thử nghiệm nhanh chóng.
- **Tải lên tệp tin CSV**: Kéo thả hoặc tải lên tệp tin `.csv` chứa lịch sử giá để tự động trích xuất cột giá đóng cửa và suy luận kết quả.

---

## Thiết Kế & Trải Nghiệm Giao Diện (UI/UX)

- **Phong cách tối giản, tinh tế (Clean & Minimalist)**: Bố cục rõ ràng, sử dụng bảng màu sắc trung tính dịu mắt (`Slate #0f172a`, `Background #f8fafc`, `Card #ffffff`), độ tương phản chuẩn mực, không gây mỏi mắt.
- **Không icon màu mè**: Thay thế các biểu tượng rườm rà bằng các nhãn văn bản mạch lạc, thẻ trạng thái đơn sắc trang nhã (*Xanh rừng thẫm* cho xu hướng Tăng, *Đỏ đô dịu* cho xu hướng Giảm, huy hiệu trực tuyến màu lục dịu).
- **Tương tác mượt mà**: Tích hợp Fetch API và Chart.js để cập nhật biểu đồ và bảng dữ liệu nhanh chóng mà không cần tải lại toàn bộ trang web.

---

## Công Nghệ Sử Dụng

- **Backend**: Python 3, Flask (Mô hình MVC), Gunicorn (WSGI Server cho Production), YFinance (Yahoo Finance API).
- **Machine Learning / AI**: TensorFlow 2.x, Keras (Stacked SimpleRNN 64-32 units), Scikit-learn (MinMaxScaler), NumPy, Pandas, Joblib.
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System), JavaScript (ES6+), Chart.js (v4.4).
- **Deployment & Cloud**: Render.com (Web Service), Git / GitHub.

---

## Hướng Dẫn Chạy Cục Bộ (Local Development)

Nếu muốn chạy ứng dụng trực tiếp trên máy tính cá nhân:

### 1. Kích hoạt môi trường và cài đặt thư viện
Yêu cầu Python 3.9 - 3.11. Kích hoạt môi trường Conda (hoặc Virtualenv):
```bash
conda activate cnn_env
# Hoặc cài đặt gói phụ thuộc nếu thiết lập môi trường mới:
pip install -r requirements.txt
```

> **Lưu ý cho VS Code / IDE:** Thư mục `.vscode/settings.json` đã được thiết lập sẵn Interpreter trỏ tới môi trường `cnn_env` để trình soạn thảo nhận diện đúng các thư viện `flask` và `tensorflow` (không bị gạch chân đỏ cảnh báo import).

### 2. Khởi động ứng dụng
Chạy trực tiếp file `app.py` từ Terminal:
```bash
python app.py
```

### 3. Truy cập hệ thống
Sau khi máy chủ khởi động và nạp dữ liệu/mô hình vào bộ nhớ RAM, mở trình duyệt web và truy cập:
👉 **`http://127.0.0.1:5000`** *(hoặc `http://localhost:5000`)*