from flask import Flask, session
from .utils import convert_currency_to_int, convert_int_to_currency
from flask_mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', "your_very_long_and_random_secret_key_1234567890")

    # Đăng ký blueprints
    from .views import views
    from .auth import auth
    from .admin import admin

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(admin, url_prefix="/admin")

    # Context processor cho toàn bộ ứng dụng
    @app.context_processor
    def utility_processor():
        return dict(convert_currency_to_int=convert_currency_to_int, convert_int_to_currency=convert_int_to_currency)

    # Cấu hình Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '15082004qwerty@gmail.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'cnau sqsg pvap hsxb')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '15082004qwerty@gmail.com')

    # Context processor để cung cấp thông tin người dùng
    @app.context_processor
    def user_processor():
        user_name = None
        is_admin = False
        if 'current_user' in session:
            user_name = session['current_user'].get('name')
            is_admin = session['current_user'].get('admin') == 1
        return dict(user_name=user_name, is_admin=is_admin)

    # Khởi tạo Flask-Mail
    mail = Mail(app)
    app.mail = mail

    return app