"""
Module: stock_controller.py
Vai trò trong MVC: Controller
Đảm nhận: Tiếp nhận yêu cầu HTTP (Web & REST API), xác thực tham số đầu vào,
gọi các hàm xử lý từ tầng Model (StockPredictor, StockDataLoader),
và chuyển dữ liệu tới tầng View để hiển thị.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models.predictor import StockPredictor
from models.data_loader import StockDataLoader
import config

stock_bp = Blueprint('stock', __name__)

# Khởi tạo các đối tượng Model
predictor = StockPredictor.get_instance()
data_loader = StockDataLoader.get_instance()

# Bộ nhớ đệm kết quả đánh giá để tăng tốc độ phản hồi
_cached_evaluation = None


# ==============================================================================
# 1. CÁC ĐƯỜNG DẪN GIAO DIỆN (VIEW RENDERING ROUTES)
# ==============================================================================

@stock_bp.route('/')
def index():
    """Trang chủ: Bảng điều khiển dự báo giá cổ phiếu."""
    symbol = request.args.get('symbol', config.DEFAULT_SYMBOL)
    forecast_days = int(request.args.get('days', 7))

    popular_stocks = data_loader.get_popular_stocks()
    model_summary = predictor.get_model_summary()

    try:
        # Lấy dữ liệu 60 phiên gần nhất từ Model
        recent_data = data_loader.get_last_n_days(symbol, n=config.TIME_STEPS)
        closes = recent_data["close_prices"]

        # Dự báo n ngày tiếp theo
        is_aapl = (symbol == "AAPL")
        predictions = predictor.predict_multistep(
            closes, 
            n_days=forecast_days, 
            dynamic_scale=not is_aapl
        )

        latest_price = recent_data["latest_price"]
        next_pred_price = predictions[0]["predicted_price"] if predictions else latest_price
        day1_diff = next_pred_price - latest_price
        day1_pct = (day1_diff / latest_price * 100) if latest_price else 0

        initial_data = {
            "symbol": symbol,
            "forecast_days": forecast_days,
            "recent_data": recent_data,
            "predictions": predictions,
            "latest_price": latest_price,
            "next_pred_price": next_pred_price,
            "day1_diff": round(day1_diff, 2),
            "day1_pct": round(day1_pct, 2),
            "trend": "Tăng" if day1_diff > 0 else ("Giảm" if day1_diff < 0 else "Đi ngang")
        }
    except Exception as e:
        initial_data = {"error": str(e), "symbol": symbol, "forecast_days": forecast_days}

    return render_template(
        'index.html',
        popular_stocks=popular_stocks,
        model_summary=model_summary,
        initial_data=initial_data,
        active_tab='dashboard'
    )


@stock_bp.route('/evaluate')
def evaluate():
    """Chuyển hướng về trang chủ do đã lược bỏ phần đánh giá mô hình."""
    return redirect(url_for('stock.index'))


@stock_bp.route('/custom')
def custom_forecast():
    """Trang dự báo tùy biến: Cho phép người dùng nhập 60 giá hoặc tải file CSV."""
    model_summary = predictor.get_model_summary()
    return render_template(
        'custom.html',
        model_summary=model_summary,
        active_tab='custom'
    )


# ==============================================================================
# 2. CÁC ĐƯỜNG DẪN API DỮ LIỆU (REST API ENDPOINTS)
# ==============================================================================

@stock_bp.route('/api/stock/<symbol>')
def api_get_stock_forecast(symbol):
    """API lấy dữ liệu lịch sử và kết quả dự báo của một mã cổ phiếu."""
    try:
        days = int(request.args.get('days', 7))
        recent_data = data_loader.get_last_n_days(symbol, n=config.TIME_STEPS)
        closes = recent_data["close_prices"]

        is_aapl = (symbol == "AAPL")
        predictions = predictor.predict_multistep(
            closes, 
            n_days=days, 
            dynamic_scale=not is_aapl
        )

        latest_price = recent_data["latest_price"]
        next_pred = predictions[0]["predicted_price"] if predictions else latest_price
        diff = round(next_pred - latest_price, 2)
        pct = round((diff / latest_price * 100), 2) if latest_price else 0

        return jsonify({
            "success": True,
            "symbol": symbol,
            "dates": recent_data["dates"],
            "close_prices": closes,
            "latest_price": latest_price,
            "next_pred_price": next_pred,
            "diff": diff,
            "pct": pct,
            "trend": "Tăng" if diff > 0 else ("Giảm" if diff < 0 else "Đi ngang"),
            "predictions": predictions
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@stock_bp.route('/api/predict-custom', methods=['POST'])
def api_predict_custom():
    """API nhận mảng số hoặc chuỗi text từ người dùng để dự báo."""
    try:
        req = request.get_json(force=True)
        raw_text = req.get('text', '')
        days = int(req.get('days', 7))

        prices = data_loader.parse_custom_text(raw_text)

        predictions = predictor.predict_multistep(
            prices, 
            n_days=days, 
            dynamic_scale=True
        )

        last_60 = prices[-config.TIME_STEPS:]
        latest_price = round(last_60[-1], 2)
        next_pred = predictions[0]["predicted_price"] if predictions else latest_price
        diff = round(next_pred - latest_price, 2)
        pct = round((diff / latest_price * 100), 2) if latest_price else 0

        return jsonify({
            "success": True,
            "count_provided": len(prices),
            "historical_subset": [round(p, 2) for p in last_60],
            "latest_price": latest_price,
            "next_pred_price": next_pred,
            "diff": diff,
            "pct": pct,
            "trend": "Tăng" if diff > 0 else ("Giảm" if diff < 0 else "Đi ngang"),
            "predictions": predictions
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@stock_bp.route('/api/upload-csv', methods=['POST'])
def api_upload_csv():
    """API tải lên file CSV để trích xuất dữ liệu giá và chạy dự báo."""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "Vui lòng chọn tệp CSV."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "Chưa chọn tệp tin."}), 400

        days = int(request.form.get('days', 7))
        parsed = data_loader.parse_csv_file(file)
        prices = parsed["prices"]

        predictions = predictor.predict_multistep(
            prices, 
            n_days=days, 
            dynamic_scale=True
        )

        last_60 = prices[-config.TIME_STEPS:]
        latest_price = round(last_60[-1], 2)
        next_pred = predictions[0]["predicted_price"] if predictions else latest_price
        diff = round(next_pred - latest_price, 2)
        pct = round((diff / latest_price * 100), 2) if latest_price else 0

        return jsonify({
            "success": True,
            "filename": file.filename,
            "column_used": parsed["column_used"],
            "total_rows": len(prices),
            "dates": parsed["dates"],
            "historical_subset": [round(p, 2) for p in last_60],
            "latest_price": latest_price,
            "next_pred_price": next_pred,
            "diff": diff,
            "pct": pct,
            "trend": "Tăng" if diff > 0 else ("Giảm" if diff < 0 else "Đi ngang"),
            "predictions": predictions
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@stock_bp.route('/api/sample-data')
def api_sample_data():
    """API cung cấp sẵn 60 mức giá thực tế mẫu để người dùng thử nghiệm nhanh."""
    try:
        sample = data_loader.get_last_n_days("AAPL", n=config.TIME_STEPS)
        formatted_str = ", ".join([str(p) for p in sample["close_prices"]])
        return jsonify({
            "success": True,
            "symbol": "AAPL",
            "count": len(sample["close_prices"]),
            "text": formatted_str,
            "prices": sample["close_prices"]
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
