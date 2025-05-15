from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from models import db, User
from rental_views import rental_views
from views import views
from customer_views import customer_views
from user_views import user_views
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Cấu hình SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Thay bằng key an toàn trong production

# Khởi tạo database
db.init_app(app)

# Khởi tạo Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'views.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Đăng ký Blueprints
app.register_blueprint(views)            # API quản lý sách và login
app.register_blueprint(customer_views)   # API quản lý khách hàng
app.register_blueprint(rental_views)     # API quản lý đơn thuê
app.register_blueprint(user_views)       # API quản lý nhân viên (admin)

# Redirect root to login if not authenticated
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('user_views.manage_users'))
        return redirect(url_for('views.manage_books'))
    return redirect(url_for('views.login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Tạo database nếu chưa có
        # Tạo tài khoản admin mặc định nếu chưa tồn tại
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)