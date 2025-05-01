
from flask import Blueprint, request, jsonify, render_template
from models import db, Rental, RentalDetail, Book, Customer
from datetime import datetime

# Tạo Blueprint cho quản lý đơn thuê
rental_views = Blueprint('rental_views', __name__)

# API hiển thị trang tạo đơn thuê
@rental_views.route('/add_rentals')
def add_rentals():
    return render_template('add_rentals.html')



##### API tạo đơn thuê mới   *******QUAN TRỌNG
@rental_views.route('/rentals', methods=['POST'])
def create_rental():
    """
    API tạo đơn thuê sách.
    - Nếu khách hàng chưa có, sẽ tự động tạo khách hàng mới, cập nhật vào bảng Customer
    - Kiểm tra số lượng sách có đủ để thuê hay không
    - Giảm số lượng sách trong kho.
    - Tạo đơn thuê + chi tiết đơn thuê.
    """

    data = request.get_json()

    # 1️/ Kiểm tra hoặc tạo khách hàng
    customer = Customer.query.filter_by(phone=data['customer_phone']).first()
    if not customer:
        customer = Customer(name=data['customer_name'], phone=data['customer_phone'])
        db.session.add(customer)
        db.session.commit()

    # 2️/ Tạo đơn thuê mới
    new_rental = Rental(
        customer_id=customer.id,
        rental_date=datetime.utcnow(),
        total_price=0  # Tạm thời 0, sẽ cập nhật sau
    )
    db.session.add(new_rental)
    db.session.commit()

    # 3/ Thêm sách vào đơn thuê
    total_price = 0
    rental_details = []
    for item in data['books']:
        book = Book.query.get(item['book_id'])

        # Kiểm tra sách có đủ số lượng để thuê không
        if not book or book.quantity < item['rental_quantity']:
            return jsonify({'message': f'Sách "{book.title}" không đủ số lượng!'}), 400

        # Giảm số lượng sách trong kho
        book.quantity -= item['rental_quantity']

        # Tính tổng tiền thuê
        total_price += book.rental_price * item['rental_quantity']

        # Tạo chi tiết đơn thuê
        rental_detail = RentalDetail(
            rental_id=new_rental.id,
            book_id=book.id,
            rental_quantity=item['rental_quantity'],
            return_due_date=datetime.strptime(item['return_due_date'], "%Y-%m-%d")  # Tự chọn ngày trả dự kiến
        )
        rental_details.append(rental_detail)
        db.session.add(rental_detail)

    # 4/ Cập nhật tổng tiền thuê vào đơn thuê
    new_rental.total_price = total_price
    db.session.commit()

    return jsonify({
        'message': 'Đơn thuê đã được tạo thành công!',
        'rental_id': new_rental.id,
        'customer': {'id': customer.id, 'name': customer.name, 'phone': customer.phone},
        'total_price': total_price,
        'books': [{'book_id': detail.book_id, 'quantity': detail.rental_quantity} for detail in rental_details]
    }), 201




###### API QUẢN LÝ ĐƠN THUÊ **** QUAN TRỌNG

# API hiển thị trang quản lý đơn thuê
@rental_views.route('/manage_rentals')
def manage_rentals():
    return render_template('manage_rentals.html')


# API hiển thị danh sách đơn thuê, bảng rental ko có customer_name, join với customer thông qua customer_id
@rental_views.route('/rentals', methods=['GET'])
def get_all_rentals():
    rentals = Rental.query.all()  # Truy vấn tất cả các đơn thuê từ bảng Rental
    rental_list = []

    for rental in rentals:
        # Lấy thông tin khách hàng từ bảng Customer
        customer = Customer.query.get(rental.customer_id)  # Truy vấn khách hàng theo customer_id

        rental_data = {
            "id": rental.id,
            "customer_name": customer.name if customer else "Không có tên khách hàng",  # Trả tên khách hàng
            "rental_date": rental.rental_date.strftime('%Y-%m-%d %H:%M:%S'),
            "return_date": rental.return_date.strftime('%Y-%m-%d %H:%M:%S') if rental.return_date else None,
            "status": rental.status,
            "total_price": rental.total_price
        }
        rental_list.append(rental_data)

    return jsonify(rental_list)



# Tìm đơn thuê theo số điện thoại
@rental_views.route('/rentals/search', methods=['GET'])
def search_rentals():
    phone = request.args.get('phone')
    customer = Customer.query.filter_by(phone=phone).first()
    if not customer:
        return jsonify([])

    rentals = Rental.query.filter_by(customer_id=customer.id).all()
    result = []
    for rental in rentals:
        result.append({
            'id': rental.id,
            'customer_name': customer.name,
            'rental_date': rental.rental_date.strftime('%Y-%m-%d'),
            'status': rental.status,
            'total_price': rental.total_price
        })
    return jsonify(result)

# Cập nhật trạng thái đơn thuê và hoàn trả sách    ***** QUAN TRỌNG
@rental_views.route('/rentals/<int:rental_id>/complete', methods=['POST'])
def complete_rental(rental_id):
    rental = Rental.query.get(rental_id)
    if not rental or rental.status == 'completed':
        return jsonify({'message': 'Đơn không tồn tại hoặc đã hoàn tất'}), 400

    rental.status = 'completed'
    rental.return_date = datetime.utcnow()

    # Trả từng quyển sách
    details = RentalDetail.query.filter_by(rental_id=rental.id).all()
    for detail in details:
        book = Book.query.get(detail.book_id)
        book.quantity += detail.rental_quantity
        detail.is_returned = True
        detail.returned_date = datetime.utcnow()

    db.session.commit()
    return jsonify({'message': 'Đã hoàn tất đơn thuê và cập nhật kho sách'})

# API lấy chi tiết đơn thuê
@rental_views.route('/rentals/<int:rental_id>/details', methods=['GET'])
def get_rental_details(rental_id):
    details = RentalDetail.query.filter_by(rental_id=rental_id).all()
    result = []
    for detail in details:
        book = Book.query.get(detail.book_id)
        result.append({
            'book_title': book.title,
            'rental_quantity': detail.rental_quantity,
            'return_due_date': detail.return_due_date.strftime('%Y-%m-%d'),
            'returned_date': detail.returned_date.strftime('%Y-%m-%d') if detail.returned_date else None,
            'is_returned': detail.is_returned
        })
    return jsonify(result)
