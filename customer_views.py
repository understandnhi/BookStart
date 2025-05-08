from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Customer, Rental
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    try:
        customers = Customer.query.filter_by(is_deleted=False).all()
        if not customers:
            logger.info("No customers found")
            return jsonify({'message': 'Không có khách hàng nào'}), 404
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'phone': c.phone
        } for c in customers]), 200
    except Exception as e:
        logger.error(f"Error retrieving customers: {str(e)}")
        return jsonify({'message': f'Lỗi khi lấy danh sách khách hàng: {str(e)}'}), 500

# API lấy thông tin một khách hàng cụ thể
@customer_views.route('/customer/<int:id>', methods=['GET'])
@login_required
def get_customer(id):
    try:
        customer = Customer.query.filter_by(id=id, is_deleted=False).first()
        if not customer:
            logger.warning(f"Customer ID {id} not found or deleted")
            return jsonify({'message': 'Khách hàng không tồn tại hoặc đã bị xóa'}), 404
        return jsonify({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving customer ID {id}: {str(e)}")
        return jsonify({'message': f'Lỗi khi lấy thông tin khách hàng: {str(e)}'}), 500

# API tìm kiếm khách hàng theo tên hoặc số điện thoại
@customer_views.route('/search_customer', methods=['GET'])
@login_required
def search_customer():
    try:
        query = request.args.get('query', '').strip()
        if not query:
            logger.warning("Empty search query provided")
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
            } for c in customers]), 200
        logger.info(f"No customers found for query: {query}")
        return jsonify({'message': 'Không tìm thấy khách hàng!'}), 404
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return jsonify({'message': f'Lỗi khi tìm kiếm khách hàng: {str(e)}'}), 500

# API thêm khách hàng mới
@customer_views.route('/add_customer', methods=['POST'])
@login_required
def add_customer():
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'phone' not in data:
            logger.warning("Invalid customer data provided")
            return jsonify({'message': 'Vui lòng cung cấp tên và số điện thoại!'}), 400

        # Kiểm tra định dạng số điện thoại (10 chữ số)
        if not data['phone'].isdigit() or len(data['phone']) != 10:
            logger.warning(f"Invalid phone number format: {data['phone']}")
            return jsonify({'message': 'Số điện thoại phải có 10 chữ số!'}), 400

        # Kiểm tra số điện thoại đã tồn tại
        existing_customer = Customer.query.filter_by(phone=data['phone'], is_deleted=False).first()
        if existing_customer:
            logger.warning(f"Phone number {data['phone']} already in use")
            return jsonify({'message': 'Số điện thoại đã được sử dụng!'}), 400

        new_customer = Customer(name=data['name'], phone=data['phone'], is_deleted=False)
        db.session.add(new_customer)
        db.session.commit()
        logger.info(f"Created customer ID {new_customer.id}")
        return jsonify({
            'message': 'Khách hàng được thêm thành công!',
            'id': new_customer.id
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating customer: {str(e)}")
        return jsonify({'message': 'Lỗi server khi thêm khách hàng'}), 500

# API cập nhật thông tin khách hàng
@customer_views.route('/update_customer/<int:id>', methods=['PUT'])
@login_required
def update_customer(id):
    try:
        customer = Customer.query.filter_by(id=id, is_deleted=False).first()
        if not customer:
            logger.warning(f"Customer ID {id} not found or deleted")
            return jsonify({'message': 'Khách hàng không tồn tại hoặc đã bị xóa'}), 404

        data = request.get_json()
        if not data:
            logger.warning("No update data provided")
            return jsonify({'message': 'Không có dữ liệu cập nhật!'}), 400

        # Kiểm tra định dạng số điện thoại nếu được cung cấp
        new_phone = data.get('phone', customer.phone)
        if new_phone != customer.phone:
            if not new_phone.isdigit() or len(new_phone) != 10:
                logger.warning(f"Invalid phone number format: {new_phone}")
                return jsonify({'message': 'Số điện thoại phải có 10 chữ số!'}), 400
            existing_customer = Customer.query.filter_by(phone=new_phone, is_deleted=False).first()
            if existing_customer:
                logger.warning(f"Phone number {new_phone} already in use")
                return jsonify({'message': 'Số điện thoại đã được sử dụng!'}), 400

        customer.name = data.get('name', customer.name)
        customer.phone = new_phone
        db.session.commit()
        logger.info(f"Updated customer ID {id}")
        return jsonify({'message': 'Thông tin khách hàng đã được cập nhật!'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating customer ID {id}: {str(e)}")
        return jsonify({'message': 'Lỗi server khi cập nhật khách hàng'}), 500

# API xóa mềm khách hàng
@customer_views.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete_customer(id):
    try:
        customer = Customer.query.get(id)
        if not customer:
            logger.warning(f"Customer ID {id} not found")
            return jsonify({'message': 'Khách hàng không tồn tại!'}), 404

        if customer.is_deleted:
            logger.warning(f"Customer ID {id} already deleted")
            return jsonify({'message': 'Khách hàng đã được xóa trước đó!'}), 400

        # Kiểm tra xem khách hàng có đơn thuê active hoặc overdue
        incomplete_rentals = Rental.query.filter_by(customer_id=id).filter(Rental.status.in_(['active', 'overdue'])).count()
        if incomplete_rentals > 0:
            logger.warning(f"Customer ID {id} has {incomplete_rentals} active or overdue rentals")
            return jsonify({'message': 'Không thể xóa khách hàng vì còn đơn thuê active hoặc quá hạn!'}), 400

        # Xóa mềm
        customer.is_deleted = True
        db.session.commit()
        logger.info(f"Deleted customer ID {id}")
        return jsonify({'message': 'Khách hàng đã được xóa thành công!'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting customer ID {id}: {str(e)}")
        return jsonify({'message': f'Lỗi khi xóa khách hàng: {str(e)}'}), 500
