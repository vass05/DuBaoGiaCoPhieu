"""
Module: data_loader.py
Vai trò trong MVC: Model
Đảm nhận: Đọc và quản lý tập dữ liệu tài chính, trích xuất chuỗi thời gian của các mã cổ phiếu,
xử lý dữ liệu tùy chỉnh do người dùng nhập hoặc tải lên từ tệp tin CSV.
"""

import os
import io
import sys
import pandas as pd
import numpy as np
import config

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Danh mục các công ty tiêu biểu kèm tên hiển thị trực quan
POPULAR_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "is_trained": True},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "is_trained": False},
    {"symbol": "GOOGL", "name": "Alphabet Inc. (Google)", "is_trained": False},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "is_trained": False},
    {"symbol": "FB", "name": "Meta Platforms (Facebook)", "is_trained": False},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "is_trained": False},
    {"symbol": "IBM", "name": "IBM Corporation", "is_trained": False},
    {"symbol": "INTC", "name": "Intel Corporation", "is_trained": False},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "is_trained": False},
    {"symbol": "AAL", "name": "American Airlines Group", "is_trained": False},
]


class StockDataLoader:
    """Lớp nạp và chuẩn bị dữ liệu tài chính cho mô hình MVC."""

    _instance = None
    _df_cache = None
    _grouped_cache = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, data_path=None):
        self.data_path = data_path or config.DATA_PATH

    def _get_dataframe(self):
        """Tải dữ liệu 5 năm vào bộ nhớ đệm (Cache) và lập chỉ mục O(1) theo mã cổ phiếu."""
        if StockDataLoader._df_cache is None:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"Không tìm thấy tập dữ liệu: {self.data_path}")
            print(f"[StockDataLoader] Loading dataset: {self.data_path}...")
            df = pd.read_csv(self.data_path)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(['Name', 'date'])
            StockDataLoader._df_cache = df
            # Lập chỉ mục sẵn vào từ điển theo mã để tra cứu tức thì O(1)
            StockDataLoader._grouped_cache = {
                sym: group.copy() for sym, group in df.groupby('Name')
            }
            print(f"[StockDataLoader] Loaded {len(df):,} rows and indexed {len(StockDataLoader._grouped_cache)} symbols.")
        return StockDataLoader._df_cache

    def get_popular_stocks(self):
        """Trả về danh sách các mã cổ phiếu phổ biến."""
        return POPULAR_STOCKS

    def get_all_symbols(self):
        """Trả về toàn bộ danh sách mã cổ phiếu có trong tập dữ liệu."""
        self._get_dataframe()
        return sorted(list(StockDataLoader._grouped_cache.keys()))

    def get_stock_data(self, symbol="AAPL"):
        """Lấy toàn bộ dữ liệu lịch sử giá của một mã cổ phiếu cụ thể (tra cứu tức thì O(1))."""
        self._get_dataframe()
        sub_df = StockDataLoader._grouped_cache.get(symbol)
        if sub_df is None or sub_df.empty:
            raise ValueError(f"Không tìm thấy mã cổ phiếu: {symbol}")
        return sub_df

    def get_last_n_days(self, symbol="AAPL", n=60):
        """Trích xuất n phiên giao dịch gần nhất của mã cổ phiếu."""
        sub_df = self.get_stock_data(symbol)
        recent = sub_df.tail(n)

        dates = recent['date'].dt.strftime('%Y-%m-%d').tolist()
        closes = recent['close'].round(2).tolist()
        opens = recent['open'].round(2).tolist() if 'open' in recent.columns else []
        highs = recent['high'].round(2).tolist() if 'high' in recent.columns else []
        lows = recent['low'].round(2).tolist() if 'low' in recent.columns else []
        volumes = recent['volume'].tolist() if 'volume' in recent.columns else []

        return {
            "symbol": symbol,
            "count": len(closes),
            "dates": dates,
            "close_prices": closes,
            "open_prices": opens,
            "high_prices": highs,
            "low_prices": lows,
            "volumes": volumes,
            "latest_price": closes[-1] if closes else 0,
            "latest_date": dates[-1] if dates else ""
        }

    def parse_custom_text(self, text):
        """
        Phân tách chuỗi số do người dùng nhập (ngăn cách bởi dấu phẩy, khoảng trắng hoặc dòng mới).
        Trả về danh sách số thực.
        """
        # Thay thế dấu phẩy, chấm phẩy, tab, xuống dòng thành khoảng trắng
        cleaned = text.replace(',', ' ').replace(';', ' ').replace('\n', ' ').replace('\r', ' ')
        tokens = cleaned.split()
        prices = []
        for t in tokens:
            try:
                val = float(t.strip())
                prices.append(val)
            except ValueError:
                continue

        if len(prices) < config.TIME_STEPS:
            raise ValueError(
                f"Bạn đã nhập {len(prices)} giá trị. Cần tối thiểu {config.TIME_STEPS} giá đóng cửa để mô hình dự báo."
            )
        return prices

    def parse_csv_file(self, file_storage):
        """
        Đọc tệp tin CSV do người dùng tải lên, tự động nhận diện cột giá đóng cửa.
        """
        try:
            content = file_storage.read()
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Không thể đọc file CSV: {e}")

        # Tìm cột giá phù hợp
        candidate_cols = ['close', 'Close', 'price', 'Price', 'gia_dong_cua', 'Gia']
        target_col = None
        for col in candidate_cols:
            if col in df.columns:
                target_col = col
                break

        if target_col is None:
            # Chọn cột số đầu tiên có nhiều giá trị hợp lệ
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                target_col = numeric_cols[0]
            else:
                raise ValueError("Không tìm thấy cột dữ liệu số hợp lệ trong file CSV.")

        prices = df[target_col].dropna().astype(float).tolist()
        if len(prices) < config.TIME_STEPS:
            raise ValueError(
                f"File CSV có {len(prices)} dòng dữ liệu hợp lệ. Cần tối thiểu {config.TIME_STEPS} dòng để chạy dự báo."
            )

        # Lấy ngày nếu có
        dates = []
        date_candidates = ['date', 'Date', 'ngay', 'time', 'Time']
        for dcol in date_candidates:
            if dcol in df.columns:
                dates = df[dcol].astype(str).tolist()
                break

        return {
            "column_used": target_col,
            "prices": prices,
            "dates": dates[-config.TIME_STEPS:] if dates else []
        }
