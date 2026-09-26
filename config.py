import os

# Đường dẫn thư mục gốc
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn tài nguyên Model và Dữ liệu
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'rnn_stock_model.keras')
SCALER_PATH = os.path.join(BASE_DIR, 'models', 'stock_scaler.pkl')
DATA_PATH = os.path.join(BASE_DIR, 'DATA', 'Stock_Market_Data', 'all_stocks_5yr.csv')

# Tham số cấu hình mô hình
TIME_STEPS = 60
DEFAULT_SYMBOL = 'AAPL'

# Cấu hình Web Server (Tự động nhận PORT từ Render.com)
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
