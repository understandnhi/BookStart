
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
from dateutil import parser  # Thêm thư viện để xử lý ngày linh hoạt
from datetime import datetime
import pytz

@rental_views.route('/rentals', methods=['POST'])
def create_rental():
    data = request.get_json()

    try:
        # Thiết lập múi giờ Việt Nam (UTC+7)
        vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')

        # 1️/ Kiểm tra hoặc tạo khách hàng
        customer = Customer.query.filter_by(phone=data['customer_phone']).first()
        if not customer:
            customer = Customer(name=data['customer_name'], phone=data['customer_phone'])
            db.session.add(customer)

        # 2️/ Kiểm tra danh sách sách trước khi tạo đơn thuê
        total_price = 0
        rental_details = []
        books_to_update = []

        for item in data['books']:
            book = Book.query.get(item['book_id'])
            if not book:
                db.session.rollback()
                return jsonify({'message': f'Sách với ID {item["book_id"]} không tồn tại!'}), 400

            rental_quantity = item.get('rental_quantity', 1)
            if rental_quantity < 1:
                db.session.rollback()
                return jsonify({'message': f'Số lượng thuê của sách "{book.title}" phải lớn hơn 0!'}), 400

            if book.quantity < rental_quantity:
                db.session.rollback()
                return jsonify({'message': f'Sách "{book.title}" không đủ số lượng!'}), 400

            try:
                return_due_date = parser.parse(item['return_due_date']).replace(tzinfo=vn_timezone)
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({'message': f'Ngày trả dự kiến "{item["return_due_date"]}" không hợp lệ!'}), 400

            books_to_update.append((book, rental_quantity))
            total_price += book.rental_price * rental_quantity

            rental_detail = RentalDetail(
                book_id=book.id,
                rental_quantity=rental_quantity,
                return_due_date=return_due_date
            )
            rental_details.append(rental_detail)

        # 3️/ Tạo đơn thuê mới
        new_rental = Rental(
            customer_id=customer.id,
            rental_date=datetime.now(vn_timezone),  # Sử dụng giờ Việt Nam
            total_price=total_price
        )
        db.session.add(new_rental)
        db.session.flush()

        # 4️/ Gán rental_id cho các chi tiết đơn thuê
        for detail in rental_details:
            detail.rental_id = new_rental.id
            db.session.add(detail)

        # 5️/ Giảm số lượng sách trong kho
        for book, quantity in books_to_update:
            book.quantity -= quantity

        # 6️/ Commit tất cả thay đổi
        db.session.commit()

        return jsonify({
            'message': 'Đơn thuê đã được tạo thành công!',
            'rental_id': new_rental.id,
            'customer': {'id': customer.id, 'name': customer.name, 'phone': customer.phone},
            'total_price': total_price,
            'books': [{'book_id': detail.book_id, 'quantity': detail.rental_quantity} for detail in rental_details]
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo đơn thuê: {str(e)}'}), 500



###### API QUẢN LÝ ĐƠN THUÊ **** QUAN TRỌNG

# API hiển thị trang quản lý đơn thuê
@rental_views.route('/manage_rentals')
def manage_rentals():
    return render_template('manage_rentals.html')


# API hiển thị danh sách đơn thuê, bảng rental ko có customer_name, join với customer thông qua customer_id
@rental_views.route('/rentals', methods=['GET'])
def get_all_rentals():
    rentals = Rental.query.filter(Rental.total_price > 0).all()
    rental_list = []

    for rental in rentals:
        has_details = RentalDetail.query.filter_by(rental_id=rental.id).first() is not None
        if not has_details:
            continue

        customer = Customer.query.get(rental.customer_id)
        rental_data = {
            "id": rental.id,
            "customer_name": customer.name if customer else "Không có tên khách hàng",
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
    if not rental:
        return jsonify({'message': 'Đơn thuê không tồn tại'}), 404
    if rental.status == 'completed':
        return jsonify({'message': 'Đơn thuê đã hoàn tất, không thể cập nhật lại'}), 400
    if rental.status != 'active':
        return jsonify({'message': 'Đơn thuê không ở trạng thái Active'}), 400

    vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    rental.status = 'completed'
    rental.return_date = datetime.now(vn_timezone)

    details = RentalDetail.query.filter_by(rental_id=rental.id).all()
    for detail in details:
        book = Book.query.get(detail.book_id)
        if not book:
            db.session.rollback()
            return jsonify({'message': f'Sách với ID {detail.book_id} không tồn tại'}), 400
        if detail.rental_quantity <= 0:
            db.session.rollback()
            return jsonify({'message': 'Số lượng sách trả lại không hợp lệ'}), 400
        book.quantity += detail.rental_quantity
        detail.is_returned = True
        detail.returned_date = datetime.now(vn_timezone)

    try:
        db.session.commit()
        return jsonify({'message': 'Đã hoàn tất đơn thuê và cập nhật kho sách'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Lỗi server khi cập nhật đơn thuê'}), 500


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
            'return_due_date': detail.return_due_date.strftime('%Y-%m-%d %H:%M:%S'),  # Thêm giờ
            'returned_date': detail.returned_date.strftime('%Y-%m-%d %H:%M:%S') if detail.returned_date else None,  # Thêm giờ
            'is_returned': detail.is_returned
        })
    return jsonify(result)

# Kiểm tra và xóa các đơn thuê rỗng hiện có
def clean_empty_rentals():
    try:
        empty_rentals = Rental.query.filter_by(total_price=0).all()
        for rental in empty_rentals:
            # Kiểm tra xem có RentalDetail liên quan không
            details = RentalDetail.query.filter_by(rental_id=rental.id).first()
            if not details:
                db.session.delete(rental)
        db.session.commit()
        print("Đã xóa các đơn thuê rỗng.")
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi xóa đơn thuê rỗng: {str(e)}")