"""
Module: app.py
Vai trò trong MVC: Application Entry & Controller Binding
Khởi tạo Flask Server, liên kết tầng View (thư mục views/) và tầng Controller (stock_bp).
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask
from controllers.stock_controller import stock_bp
import config


def create_app():
    """Khởi tạo ứng dụng Flask theo đúng kiến trúc chuẩn MVC."""
    app = Flask(
        __name__,
        template_folder=os.path.join(config.BASE_DIR, 'views'),
        static_folder=os.path.join(config.BASE_DIR, 'static')
    )
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Đăng ký Controller Blueprint
    app.register_blueprint(stock_bp)

    return app


def warm_up():
    """Tải trước dữ liệu và mô hình AI vào RAM để phản hồi tức thì."""
    try:
        from models.data_loader import StockDataLoader
        from models.predictor import StockPredictor
        dl = StockDataLoader.get_instance()
        pred = StockPredictor.get_instance()
        aapl = dl.get_last_n_days('AAPL', 60)
        _ = pred.predict_multistep(aapl['close_prices'], n_days=1)
        print("[App Warm-Up] Model and data pre-warmed successfully!")
    except Exception as e:
        print(f"[App Warm-Up Warning] {e}")


app = create_app()
warm_up()

if __name__ == '__main__':
    print("=" * 65)
    print("   STOCK PRICE PREDICTION SYSTEM - RNN (MVC ARCHITECTURE)")
    print(f"   Server URL: http://{config.HOST}:{config.PORT}")
    print("=" * 65)
    app.run(host=config.HOST, port=config.PORT, debug=False)
