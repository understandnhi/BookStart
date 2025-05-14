#
# # models.py
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
#
# db = SQLAlchemy()
#
# # Bảng Users (Nhân viên nhà sách)
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), unique=True, nullable=False)
#     password = db.Column(db.String(100), nullable=False)
#
# # Bảng Customers (Khách hàng thuê sách)
# class Customer(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     phone = db.Column(db.String(20), unique=True, nullable=False)
#     is_deleted = db.Column(db.Boolean, default=False, nullable=False)
#
# # Bảng Books (Danh sách sách)
# class Book(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     author = db.Column(db.String(100), nullable=False)
#     quantity = db.Column(db.Integer, nullable=False, default=0)
#     rental_price = db.Column(db.Float, nullable=False)
#     is_deleted = db.Column(db.Boolean, default=False, nullable=False)
#
# # Bảng Rentals (Đơn thuê sách)
# class Rental(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
#     rental_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
#     return_date = db.Column(db.DateTime, nullable=True)
#     status = db.Column(db.String(20), nullable=False, default='active')
#     total_price = db.Column(db.Float, nullable=False, default=0.0)
#
# # Bảng Rental Details (Chi tiết đơn thuê)
# class RentalDetail(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=False)
#     book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
#     rental_quantity = db.Column(db.Integer, nullable=False, default=1)
#     return_due_date = db.Column(db.DateTime, nullable=False)
#     returned_date = db.Column(db.DateTime, nullable=True)
#     is_returned = db.Column(db.Boolean, default=False)


from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Bảng Users (Nhân viên nhà sách)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

# Bảng Customers (Khách hàng thuê sách)
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

# Bảng Books (Danh sách sách)
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    rental_price = db.Column(db.Float, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

# Bảng Rentals (Đơn thuê sách)
class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    rental_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    total_price = db.Column(db.Float, nullable=False, default=0.0)

# Bảng Rental Details (Chi tiết đơn thuê)
class RentalDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    rental_quantity = db.Column(db.Integer, nullable=False, default=1)
    return_due_date = db.Column(db.DateTime, nullable=False)
    returned_date = db.Column(db.DateTime, nullable=True)
    is_returned = db.Column(db.Boolean, default=False)