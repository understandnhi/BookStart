from flask import Blueprint, request, jsonify, render_template
from models import db, Customer

# Tạo Blueprint cho quản lý khách hàng
customer_views = Blueprint('customer_views', __name__)


# API hiển thị trang quản lý khách hàng
@customer_views.route('/manage_customers')
def manage_customers():
    return render_template('manage_customers.html')


# API lấy danh sách khách hàng
@customer_views.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    if not customers:
        return jsonify({'message': 'Không có khách hàng nào'}), 404
    return jsonify([{'id': c.id, 'name': c.name, 'phone': c.phone} for c in customers])


# API lấy thông tin một khách hàng cụ thể
@customer_views.route('/customer/<int:id>', methods=['GET'])
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return jsonify({'id': customer.id, 'name': customer.name, 'phone': customer.phone})


# API tìm kiếm khách hàng theo tên hoặc số điện thoại
@customer_views.route('/search_customer', methods=['GET'])
def search_customer():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'message': 'Vui lòng nhập tên hoặc số điện thoại để tìm kiếm!'}), 400

    customers = Customer.query.filter(
        (Customer.name.ilike(f'%{query}%')) | (Customer.phone.ilike(f'%{query}%'))
    ).all()

    if customers:
        return jsonify([{'id': c.id, 'name': c.name, 'phone': c.phone} for c in customers])
    return jsonify({'message': 'Không tìm thấy khách hàng!'}), 404


# API thêm khách hàng mới
@customer_views.route('/add_customer', methods=['POST'])
def add_customer():
    data = request.get_json()
    if not data or 'name' not in data or 'phone' not in data:
        return jsonify({'message': 'Dữ liệu không hợp lệ!'}), 400

    new_customer = Customer(name=data['name'], phone=data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': 'Khách hàng được thêm thành công!', 'id': new_customer.id}), 201


# API cập nhật thông tin khách hàng
@customer_views.route('/update_customer/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    data = request.get_json()

    if not data:
        return jsonify({'message': 'Không có dữ liệu cập nhật!'}), 400

    customer.name = data.get('name', customer.name)
    customer.phone = data.get('phone', customer.phone)
    db.session.commit()

    return jsonify({'message': 'Thông tin khách hàng đã được cập nhật!'})


# API xóa khách hàng
@customer_views.route('/delete_customer/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Khách hàng đã được xóa thành công!'})