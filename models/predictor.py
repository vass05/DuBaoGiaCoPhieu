"""
Module: predictor.py
Vai trò trong MVC: Model
Đảm nhận: Tải mô hình RNN đã huấn luyện, nạp scaler, thực hiện suy luận dự báo (Inference),
dự báo nhiều bước liên tiếp (Multi-step), và đánh giá chỉ số kiểm thử (Evaluation).
"""

import math
import os
import sys
import joblib
import numpy as np
import tensorflow as tf
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import MinMaxScaler
import config

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class StockPredictor:
    """Lớp xử lý dự báo giá cổ phiếu bằng mô hình Recurrent Neural Network (RNN)."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Áp dụng Singleton Pattern để tránh nạp lại mô hình nặng nhiều lần vào RAM."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, model_path=None, scaler_path=None, time_steps=None):
        self.model_path = model_path or config.MODEL_PATH
        self.scaler_path = scaler_path or config.SCALER_PATH
        self.time_steps = time_steps or config.TIME_STEPS

        self.model = None
        self.scaler = None
        self.is_loaded = False
        self._load_model_and_scaler()

    def _load_model_and_scaler(self):
        """Nạp trọng số mô hình .keras và bộ chuyển đổi MinMaxScaler .pkl."""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Không tìm thấy file mô hình tại: {self.model_path}")
            if not os.path.exists(self.scaler_path):
                raise FileNotFoundError(f"Không tìm thấy file scaler tại: {self.scaler_path}")

            # Nạp Keras Model và Scaler
            self.model = tf.keras.models.load_model(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.is_loaded = True
            print(f"[StockPredictor] Loaded model from: {self.model_path}")
            print(f"[StockPredictor] Loaded scaler from: {self.scaler_path}")
        except Exception as e:
            self.is_loaded = False
            print(f"[StockPredictor Error] Failed to load model: {e}")
            raise e

    def get_model_summary(self):
        """Trả về thông tin tổng quan về kiến trúc và thông số của mô hình."""
        if not self.is_loaded:
            return {"status": "Chưa nạp mô hình"}

        total_params = self.model.count_params()
        layers_info = []
        for layer in self.model.layers:
            output_shape_str = "-"
            try:
                if hasattr(layer, 'output_shape'):
                    output_shape_str = str(layer.output_shape)
            except Exception:
                pass

            layers_info.append({
                "name": layer.name,
                "type": layer.__class__.__name__,
                "output_shape": output_shape_str
            })

        min_val = float(self.scaler.data_min_[0]) if hasattr(self.scaler, 'data_min_') else 0
        max_val = float(self.scaler.data_max_[0]) if hasattr(self.scaler, 'data_max_') else 0

        return {
            "status": "Hoạt động",
            "model_type": "Stacked SimpleRNN (2 lớp ẩn RNN + 1 Dense)",
            "time_steps": self.time_steps,
            "total_params": total_params,
            "layers": layers_info,
            "trained_stock": "AAPL (Apple Inc.)",
            "feature_range": f"Min={min_val:.2f} USD, Max={max_val:.2f} USD"
        }

    def predict_next(self, prices_60, dynamic_scale=False):
        """
        Dự báo giá của 1 ngày tiếp theo từ chuỗi 60 ngày gần nhất.
        
        Tham số:
            prices_60 (list hoặc np.array): Danh sách 60 mức giá đóng cửa.
            dynamic_scale (bool): Tự thích ứng tỷ lệ nếu dữ liệu ngoài biên độ chuẩn của AAPL.
        
        Trả về:
            float: Giá dự đoán của ngày tiếp theo.
        """
        if len(prices_60) < self.time_steps:
            raise ValueError(f"Dữ liệu cần tối thiểu {self.time_steps} ngày để thực hiện dự báo.")

        # Lấy chính xác 60 ngày cuối cùng
        seq = np.array(prices_60[-self.time_steps:], dtype=float).reshape(-1, 1)

        active_scaler = self.scaler
        if dynamic_scale:
            # Tạo bộ scale cục bộ cho chuỗi dữ liệu khác dải biên độ AAPL
            active_scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_seq = active_scaler.fit_transform(seq)
        else:
            scaled_seq = active_scaler.transform(seq)

        # Định dạng Tensor 3D: (1 mẫu, 60 time_steps, 1 feature)
        tensor_input = scaled_seq.reshape(1, self.time_steps, 1)
        pred_scaled = self.model.predict(tensor_input, verbose=0)
        pred_real = active_scaler.inverse_transform(pred_scaled)

        return float(pred_real[0, 0])

    def predict_multistep(self, prices_60, n_days=7, dynamic_scale=False):
        """
        Dự báo chuỗi n_days ngày liên tiếp trong tương lai bằng kỹ thuật cửa sổ cuốn chiếu (Autoregressive Roll).
        
        Tham số:
            prices_60 (list hoặc np.array): Chuỗi 60 giá đóng cửa gần nhất.
            n_days (int): Số ngày muốn dự đoán tương lai (ví dụ 1, 3, 7, 14, 30).
            dynamic_scale (bool): Tự thích ứng tỷ lệ.
            
        Trả về:
            list: Danh sách các dict chứa chi tiết từng bước dự báo.
        """
        if len(prices_60) < self.time_steps:
            raise ValueError(f"Dữ liệu cần tối thiểu {self.time_steps} ngày.")

        current_window = list(np.array(prices_60[-self.time_steps:], dtype=float))
        last_price = float(current_window[-1])
        results = []

        active_scaler = self.scaler
        if dynamic_scale:
            active_scaler = MinMaxScaler(feature_range=(0, 1))
            active_scaler.fit(np.array(current_window).reshape(-1, 1))

        # Lưu lại cửa sổ scaled để thực hiện rolling nhanh chóng
        scaled_window = list(active_scaler.transform(np.array(current_window).reshape(-1, 1)).flatten())

        prev_p = last_price
        for step in range(1, n_days + 1):
            # Lấy 60 giá trị gần nhất trong mảng scaled
            cur_seq = np.array(scaled_window[-self.time_steps:], dtype=float).reshape(1, self.time_steps, 1)
            pred_s = self.model.predict(cur_seq, verbose=0)[0, 0]

            # Thêm giá trị vừa dự báo vào cửa sổ scaled cho bước tiếp theo
            scaled_window.append(pred_s)

            # Quy đổi ngược về tiền tệ USD thực
            pred_real_val = float(active_scaler.inverse_transform([[pred_s]])[0, 0])

            change = pred_real_val - prev_p
            pct_change = (change / prev_p) * 100 if prev_p != 0 else 0

            trend = "Tăng" if change > 0.05 else ("Giảm" if change < -0.05 else "Đi ngang")

            results.append({
                "step": step,
                "predicted_price": round(pred_real_val, 2),
                "change": round(change, 2),
                "change_percent": round(pct_change, 2),
                "trend": trend
            })

            prev_p = pred_real_val

        return results

    def evaluate_test_set(self, full_prices, dates=None, train_ratio=0.8):
        """
        Đánh giá hiệu năng của mô hình trên tập kiểm thử (Test set 20%) theo đúng quy trình từ notebook huấn luyện.
        
        Trả về:
            dict chứa: mse, rmse, mae, r2, cùng danh sách mẫu để vẽ biểu đồ so sánh.
        """
        data = np.array(full_prices, dtype=float).reshape(-1, 1)
        train_size = int(len(data) * train_ratio)
        test_data = data[train_size:]

        if len(test_data) <= self.time_steps:
            return {"error": "Tập test quá ngắn để tạo cửa sổ 60 ngày."}

        scaled_test = self.scaler.transform(test_data)

        # Tạo chuỗi kiểm thử
        X_test, y_test = [], []
        for i in range(len(scaled_test) - self.time_steps):
            X_test.append(scaled_test[i : (i + self.time_steps), 0])
            y_test.append(scaled_test[i + self.time_steps, 0])

        X_test = np.array(X_test)
        y_test = np.array(y_test)
        X_test_rnn = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

        # Dự báo toàn bộ tập Test
        y_pred_scaled = self.model.predict(X_test_rnn, verbose=0)

        # Chuyển ngược về USD
        y_test_real = self.scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
        y_pred_real = self.scaler.inverse_transform(y_pred_scaled).flatten()

        # Tính toán các chỉ số thống kê
        mse = mean_squared_error(y_test_real, y_pred_real)
        rmse = math.sqrt(mse)
        mae = mean_absolute_error(y_test_real, y_pred_real)
        r2 = r2_score(y_test_real, y_pred_real)

        # Lấy nhãn ngày tương ứng nếu có
        test_dates = []
        if dates is not None and len(dates) == len(full_prices):
            # Nhãn bắt đầu từ chỉ số train_size + time_steps
            test_dates = list(dates[train_size + self.time_steps:])

        return {
            "metrics": {
                "mse": round(float(mse), 4),
                "rmse": round(float(rmse), 4),
                "mae": round(float(mae), 4),
                "r2": round(float(r2), 4),
                "test_samples": int(len(y_test_real))
            },
            "actual": [round(float(v), 2) for v in y_test_real],
            "predicted": [round(float(v), 2) for v in y_pred_real],
            "dates": test_dates[:len(y_test_real)] if test_dates else [f"T+{i+1}" for i in range(len(y_test_real))]
        }
