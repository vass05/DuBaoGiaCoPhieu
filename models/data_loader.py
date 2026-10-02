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


# Danh mục các công ty tiêu biểu chọn lọc (Các tập đoàn lớn & 3 mã tiêu biểu Việt Nam)
POPULAR_STOCKS = [
    # Các công ty công nghệ lớn toàn cầu (USD)
    {"symbol": "AAPL", "name": "Apple Inc. (Mỹ)", "currency": "USD", "is_trained": True},
    {"symbol": "NVDA", "name": "NVIDIA Corporation (Mỹ)", "currency": "USD", "is_trained": False},
    {"symbol": "TSLA", "name": "Tesla Inc. (Mỹ)", "currency": "USD", "is_trained": False},
    {"symbol": "MSFT", "name": "Microsoft Corporation (Mỹ)", "currency": "USD", "is_trained": False},
    {"symbol": "GOOGL", "name": "Alphabet Inc. - Google (Mỹ)", "currency": "USD", "is_trained": False},
    {"symbol": "AMZN", "name": "Amazon.com Inc. (Mỹ)", "currency": "USD", "is_trained": False},

    # Chứng khoán Việt Nam (VND)
    {"symbol": "FPT.VN", "name": "Tập đoàn FPT (Việt Nam)", "currency": "VND", "is_trained": False},
    {"symbol": "VIC.VN", "name": "Tập đoàn Vingroup (Việt Nam)", "currency": "VND", "is_trained": False},
    {"symbol": "VNM.VN", "name": "Vinamilk (Việt Nam)", "currency": "VND", "is_trained": False},
]


class StockDataLoader:
    """Lớp nạp và chuẩn bị dữ liệu tài chính cho mô hình MVC."""

    _instance = None
    _df_cache = None
    _grouped_cache = {}
    _realtime_cache = {}

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
        """Trích xuất n phiên giao dịch gần nhất của mã cổ phiếu từ tập dữ liệu tĩnh CSV."""
        lookup_symbol = symbol.strip().upper()
        self._get_dataframe()
        # Xử lý trường hợp mã Meta Platforms trong dữ liệu 2018 là FB
        if lookup_symbol == 'META' and 'META' not in StockDataLoader._grouped_cache and 'FB' in StockDataLoader._grouped_cache:
            lookup_symbol = 'FB'

        sub_df = self.get_stock_data(lookup_symbol)
        recent = sub_df.tail(n)

        dates = recent['date'].dt.strftime('%Y-%m-%d').tolist()
        closes = recent['close'].round(2).tolist()
        opens = recent['open'].round(2).tolist() if 'open' in recent.columns else []
        highs = recent['high'].round(2).tolist() if 'high' in recent.columns else []
        lows = recent['low'].round(2).tolist() if 'low' in recent.columns else []
        volumes = recent['volume'].tolist() if 'volume' in recent.columns else []

        return {
            "symbol": symbol.strip().upper(),
            "source": "offline",
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

    def _fetch_yahoo_direct(self, symbol):
        """
        Gọi trực tiếp endpoint v8 chart của Yahoo Finance với HTTP header giả lập trình duyệt.
        Tránh bị chặn crumb/cookie khi chạy trên các máy chủ đám mây như Render/AWS.
        """
        import requests
        import datetime

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return None

        data = resp.json()
        result = data.get("chart", {}).get("result")
        if not result or len(result) == 0:
            return None

        item = result[0]
        timestamps = item.get("timestamp", [])
        quote = item.get("indicators", {}).get("quote", [{}])[0]
        closes = quote.get("close", [])
        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        volumes = quote.get("volume", [])

        clean_dates = []
        clean_closes = []
        clean_opens = []
        clean_highs = []
        clean_lows = []
        clean_volumes = []

        for i in range(len(timestamps)):
            c = closes[i] if i < len(closes) else None
            if c is not None and c > 0:
                d_str = datetime.datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
                clean_dates.append(d_str)
                clean_closes.append(round(float(c), 2))
                clean_opens.append(round(float(opens[i]), 2) if i < len(opens) and opens[i] is not None else round(float(c), 2))
                clean_highs.append(round(float(highs[i]), 2) if i < len(highs) and highs[i] is not None else round(float(c), 2))
                clean_lows.append(round(float(lows[i]), 2) if i < len(lows) and lows[i] is not None else round(float(c), 2))
                clean_volumes.append(int(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0)

        if len(clean_closes) < 60:
            return None

        return {
            "dates": clean_dates,
            "close_prices": clean_closes,
            "open_prices": clean_opens,
            "high_prices": clean_highs,
            "low_prices": clean_lows,
            "volumes": clean_volumes,
            "latest_price": clean_closes[-1],
            "latest_date": clean_dates[-1]
        }

    def get_realtime_stock_data(self, symbol="AAPL", n=60):
        """
        Lấy n phiên giao dịch thời gian thực gần nhất.
        Hỗ trợ đa tầng fallback để hoạt động ổn định trên cả môi trường đám mây (Render, Heroku, AWS):
        1. Memory Cache (5 phút)
        2. Direct Yahoo Finance API (v8 chart API với Browser User-Agent)
        3. Thư viện yfinance
        4. Tệp dữ liệu dự phòng cục bộ (DATA/realtime_backup.json)
        5. Tệp dữ liệu lịch sử CSV (all_stocks_5yr.csv)
        """
        import time
        import os

        symbol = symbol.strip().upper()
        # Chuyển đổi mã FB cũ thành mã META hiện tại nếu cần
        if symbol == 'FB':
            symbol = 'META'

        now = time.time()
        cached = StockDataLoader._realtime_cache.get(symbol)
        if cached and (now - cached['time'] < 300) and cached.get('data', {}).get('count', 0) >= n:
            return cached['data']

        raw_data = None

        # Tầng 1: Direct Yahoo Finance Chart API (vượt qua firewall/rate-limit của Render)
        try:
            raw_data = self._fetch_yahoo_direct(symbol)
        except Exception as e:
            print(f"[StockDataLoader] Direct Yahoo fetch failed for {symbol}: {e}")

        # Tầng 2: Thử qua yfinance nếu direct không thành công
        if not raw_data or len(raw_data.get("close_prices", [])) < n:
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1y')
                if hist is not None and not hist.empty and len(hist) >= n:
                    recent_hist = hist.tail(n)
                    raw_data = {
                        "dates": recent_hist.index.strftime('%Y-%m-%d').tolist(),
                        "close_prices": recent_hist['Close'].round(2).tolist(),
                        "open_prices": recent_hist['Open'].round(2).tolist() if 'Open' in recent_hist.columns else [],
                        "high_prices": recent_hist['High'].round(2).tolist() if 'High' in recent_hist.columns else [],
                        "low_prices": recent_hist['Low'].round(2).tolist() if 'Low' in recent_hist.columns else [],
                        "volumes": recent_hist['Volume'].astype(int).tolist() if 'Volume' in recent_hist.columns else [],
                        "latest_price": round(float(recent_hist['Close'].iloc[-1]), 2),
                        "latest_date": recent_hist.index[-1].strftime('%Y-%m-%d')
                    }
            except Exception as e:
                print(f"[StockDataLoader] yfinance fetch failed for {symbol}: {e}")

        # Tầng 3: Tệp dữ liệu dự phòng cục bộ (DATA/realtime_backup.json)
        if not raw_data or len(raw_data.get("close_prices", [])) < n:
            backup_file = os.path.join(os.path.dirname(self.data_path), "realtime_backup.json")
            if os.path.exists(backup_file):
                try:
                    import json
                    with open(backup_file, "r", encoding="utf-8") as f:
                        bdata = json.load(f)
                    if symbol in bdata:
                        raw_data = bdata[symbol]
                        print(f"[StockDataLoader] Using local realtime_backup for {symbol}")
                except Exception as e:
                    print(f"[StockDataLoader] Backup read error: {e}")

        # Tầng 4: Tự động chuyển sang dữ liệu lịch sử CSV (all_stocks_5yr.csv) nếu là mã có trong dataset
        if not raw_data or len(raw_data.get("close_prices", [])) < n:
            try:
                csv_data = self.get_last_n_days(symbol, n=n)
                if csv_data and csv_data.get("count", 0) >= n:
                    csv_data["source"] = "realtime"
                    return csv_data
            except Exception:
                pass

        if not raw_data or len(raw_data.get("close_prices", [])) < n:
            raise ValueError(
                f"Không đủ dữ liệu cho mã '{symbol}'. Vui lòng kiểm tra lại mã cổ phiếu hoặc thử lại sau."
            )

        closes = raw_data["close_prices"][-n:]
        dates = raw_data["dates"][-n:]
        opens = raw_data.get("open_prices", [])[-n:]
        highs = raw_data.get("high_prices", [])[-n:]
        lows = raw_data.get("low_prices", [])[-n:]
        volumes = raw_data.get("volumes", [])[-n:]

        data_result = {
            "symbol": symbol,
            "source": "realtime",
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

        StockDataLoader._realtime_cache[symbol] = {
            'time': now,
            'data': data_result
        }
        return data_result

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
