from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 📌 Bảng Users (Nhân viên nhà sách)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# 📌 Bảng Customers (Khách hàng thuê sách)
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)    # Các khách hàng ko đc trùng sdt, để còn tìm kiếm

# 📌 Bảng Books (Danh sách sách)
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    rental_price = db.Column(db.Float, nullable=False)

# 📌 Bảng Rentals (Đơn thuê sách)
class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    rental_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')   # Mặc định active khi 1 đơn mới đc tạo, completed khi đã trả
    total_price = db.Column(db.Float, nullable=False, default=0.0)  # Tổng tiền thuê ban đầu sẽ là 0

# 📌 Bảng Rental Details (Chi tiết đơn thuê)
    # 1 đơn thuê có nhiều bản ghi chi tiết
    # 1 bản ghi chi tiết là 1 đầu sách, có thể thuê nhiều quyền cho 1 đầu sách
class RentalDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    rental_quantity = db.Column(db.Integer, nullable=False, default=1)  # Số lượng thuê ít nhất bằng 1
    return_due_date = db.Column(db.DateTime, nullable=False)            # Ngày trả dự kiến, nhà sách tự nhập
    returned_date = db.Column(db.DateTime, nullable=True)  # Ngày trả sách thực tế, lấy theo time hiện tạị sau khi ấn completed cho đơn thuê
    is_returned = db.Column(db.Boolean, default=False)  # Trả hay chưa        # Đơn thuê ở active thì luôn luôn các đơn chi tiết là chưa trả
                                                                             # Đơn thuê ở completed thì luôn luôn các đơn chi tiết là đã trả
