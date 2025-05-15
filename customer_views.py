from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Customer, Rental

# Tạo Blueprint cho quản lý khách hàng
customer_views = Blueprint('customer_views', __name__)

# API hiển thị trang quản lý khách hàng
@customer_views.route('/manage_customers')
@login_required
def manage_customers():
    return render_template('manage_customers.html')

# API lấy danh sách khách hàng
@customer_views.route('/customers', methods=['GET'])
@login_required
def get_customers():
    customers = Customer.query.filter_by(is_deleted=False).all()
    if not customers:
        return jsonify({'message': 'Không có khách hàng nào'}), 404
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'phone': c.phone
    } for c in customers])

# API lấy thông tin một khách hàng cụ thể
@customer_views.route('/customer/<int:id>', methods=['GET'])
@login_required
def get_customer(id):
    customer = Customer.query.filter_by(id=id, is_deleted=False).first()
    if not customer:
        return jsonify({'message': 'Khách hàng không tồn tại hoặc đã bị xóa'}), 404
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'phone': customer.phone
    })

# API tìm kiếm khách hàng
@customer_views.route('/search_customer', methods=['GET'])
@login_required
def search_customer():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'message': 'Vui lòng nhập tên hoặc số điện thoại để tìm kiếm!'}), 400

    customers = Customer.query.filter(
        (Customer.name.ilike(f'%{query}%')) | (Customer.phone.ilike(f'%{query}%')),
        Customer.is_deleted == False
    ).all()

    if customers:
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'phone': c.phone
        } for c in customers])
    return jsonify({'message': 'Không tìm thấy khách hàng!'}), 404

# API thêm khách hàng mới
@customer_views.route('/add_customer', methods=['POST'])
@login_required
def add_customer():
    data = request.get_json()
    if not data or 'name' not in data or 'phone' not in data:
        return jsonify({'message': 'Vui lòng cung cấp tên và số điện thoại!'}), 400

    existing_customer = Customer.query.filter_by(phone=data['phone'], is_deleted=False).first()
    if existing_customer:
        return jsonify({'message': 'Số điện thoại đã được sử dụng!'}), 400

    new_customer = Customer(name=data['name'], phone=data['phone'], is_deleted=False)
    try:
        db.session.add(new_customer)
        db.session.commit()
        return jsonify({
            'message': 'Khách hàng được thêm thành công!',
            'id': new_customer.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Lỗi server khi thêm khách hàng'}), 500

# API cập nhật thông tin khách hàng
@customer_views.route('/update_customer/<int:id>', methods=['PUT'])
@login_required
def update_customer(id):
    customer = Customer.query.filter_by(id=id, is_deleted=False).first()
    if not customer:
        return jsonify({'message': 'Khách hàng không tồn tại hoặc đã bị xóa'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'Không có dữ liệu cập nhật!'}), 400

    new_phone = data.get('phone', customer.phone)
    if new_phone != customer.phone:
        existing_customer = Customer.query.filter_by(phone=new_phone, is_deleted=False).first()
        if existing_customer:
            return jsonify({'message': 'Số điện thoại đã được sử dụng!'}), 400

    customer.name = data.get('name', customer.name)
    customer.phone = new_phone
    try:
        db.session.commit()
        return jsonify({'message': 'Thông tin khách hàng đã được cập nhật!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Lỗi server khi cập nhật khách hàng'}), 500

# API xóa mềm khách hàng
@customer_views.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'message': 'Khách hàng không tồn tại!'}), 404

    if customer.is_deleted:
        return jsonify({'message': 'Khách hàng đã được xóa trước đó!'}), 400

    active_rentals = Rental.query.filter_by(customer_id=id, status='active').count()
    if active_rentals > 0:
        return jsonify({'message': 'Không thể xóa khách hàng vì còn đơn thuê đang active!'}), 400

    customer.is_deleted = True
    try:
        db.session.commit()
        return jsonify({'message': 'Khách hàng đã được xóa thành công!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa khách hàng: {str(e)}'}), 500