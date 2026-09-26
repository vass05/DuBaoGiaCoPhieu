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


app = create_app()

if __name__ == '__main__':
    print("=" * 65)
    print("   STOCK PRICE PREDICTION SYSTEM - RNN (MVC ARCHITECTURE)")
    print(f"   Server URL: http://{config.HOST}:{config.PORT}")
    print("=" * 65)
    app.run(host=config.HOST, port=config.PORT, debug=False)
