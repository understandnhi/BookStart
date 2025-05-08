from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models import db, User
from rental_views import rental_views
from views import views
from customer_views import customer_views
from admin_views import admin_views
import bcrypt

app = Flask(__name__)

# Cấu hình SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'understandnhi'  # Cần thiết cho session

# Khởi tạo database
db.init_app(app)

# Cấu hình Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_views.login'

# Đăng ký Blueprint
app.register_blueprint(views)            # API quản lý sách
app.register_blueprint(customer_views)   # API quản lý khách hàng
app.register_blueprint(rental_views)     # API quản lý đơn thuê
app.register_blueprint(admin_views)      # API quản lý admin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_app():
    with app.app_context():
        db.create_all()  # Tạo database nếu chưa có
        # Khởi tạo admin mặc định
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            hashed_password = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = User(
                username='admin',
                password=hashed_password,
                name='Admin User',
                email='admin@bookstart.com',
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print('Created default admin: username=admin, password=admin')

if __name__ == '__main__':
    init_app()
    app.run(debug=True)