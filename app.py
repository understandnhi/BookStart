from flask import Flask
from models import db
from rental_views import rental_views
from views import views
from customer_views import customer_views

app = Flask(__name__)

# Cấu hình SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo database
db.init_app(app)

# Đăng ký Blueprint từ views.py
app.register_blueprint(views)            # Đăng kí API quản lý sách
app.register_blueprint(customer_views)   # Đăng ký API quản lý khách hàng
app.register_blueprint(rental_views)     # Đăng ký API quản lý đơn thuê

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Tạo database nếu chưa có
    app.run(debug=True)