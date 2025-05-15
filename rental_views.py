from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Rental, RentalDetail, Book, Customer
from datetime import datetime
from dateutil import parser
import pytz
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tạo Blueprint cho quản lý đơn thuê
rental_views = Blueprint('rental_views', __name__)

# Trang tạo đơn thuê
@rental_views.route('/add_rentals')
@login_required
def add_rentals():
    return render_template('add_rentals.html')

# API lấy thông tin sách theo ID
@rental_views.route('/books/<int:book_id>/info', methods=['GET'])
@login_required
def get_book_info(book_id):
    try:
        book = Book.query.filter_by(id=book_id, is_deleted=False).first()
        if not book:
            logger.warning(f"Book ID {book_id} not found or deleted")
            return jsonify({'message': f'Sách với ID {book_id} không tồn tại hoặc đã bị xóa'}), 404

        logger.debug(f"Retrieved book info: ID {book_id}, Title {book.title}")
        return jsonify({
            'id': book.id,
            'title': book.title,
            'rental_price': book.rental_price,
            'quantity': book.quantity
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving book info for ID {book_id}: {str(e)}")
        return jsonify({'message': f'Lỗi khi lấy thông tin sách: {str(e)}'}), 500

# API tạo đơn thuê mới
@rental_views.route('/rentals', methods=['POST'])
@login_required
def create_rental():
    data = request.get_json()
    if not data or 'customer_phone' not in data or 'customer_name' not in data or 'books' not in data:
        logger.error("Missing required fields in rental request")
        return jsonify({'message': 'Vui lòng cung cấp đầy đủ thông tin!'}), 400

    try:
        vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')

        # Kiểm tra hoặc tạo khách hàng
        customer = Customer.query.filter_by(phone=data['customer_phone'], is_deleted=False).first()
        if not customer:
            customer = Customer(name=data['customer_name'], phone=data['customer_phone'], is_deleted=False)
            db.session.add(customer)

        total_price = 0
        rental_details = []
        books_to_update = []
        book_details = []

        for item in data['books']:
            book = Book.query.filter_by(id=item['book_id'], is_deleted=False).first()
            if not book:
                db.session.rollback()
                logger.error(f"Book ID {item['book_id']} not found or deleted")
                return jsonify({'message': f'Sách với ID {item["book_id"]} không tồn tại hoặc đã bị xóa!'}), 400

            rental_quantity = item.get('rental_quantity', 1)
            if rental_quantity < 1:
                db.session.rollback()
                logger.error(f"Invalid rental quantity for book {book.title}: {rental_quantity}")
                return jsonify({'message': f'Số lượng thuê của sách "{book.title}" phải lớn hơn 0!'}), 400

            if book.quantity < rental_quantity:
                db.session.rollback()
                logger.error(f"Insufficient quantity for book {book.title}: {book.quantity} available")
                return jsonify({'message': f'Sách "{book.title}" không đủ số lượng!'}), 400

            try:
                return_due_date = parser.parse(item['return_due_date']).replace(tzinfo=vn_timezone)
            except (ValueError, TypeError):
                logger.error(f"Invalid return due date for book {book.title}: {item['return_due_date']}")
                db.session.rollback()
                return jsonify({'message': f'Ngày trả dự kiến "{item["return_due_date"]}" không hợp lệ!'}), 400

            books_to_update.append((book, rental_quantity))
            item_total = book.rental_price * rental_quantity
            total_price += item_total

            rental_detail = RentalDetail(
                book_id=book.id,
                rental_quantity=rental_quantity,
                return_due_date=return_due_date
            )
            rental_details.append(rental_detail)

            book_details.append({
                'book_id': book.id,
                'title': book.title,
                'rental_price': book.rental_price,
                'rental_quantity': rental_quantity,
                'item_total': item_total
            })

        new_rental = Rental(
            customer_id=customer.id,
            rental_date=datetime.now(vn_timezone),
            total_price=total_price
        )
        db.session.add(new_rental)
        db.session.flush()

        for detail in rental_details:
            detail.rental_id = new_rental.id
            db.session.add(detail)

        for book, quantity in books_to_update:
            book.quantity -= quantity

        db.session.commit()
        logger.info(f"Created rental ID {new_rental.id} for customer {customer.name}")
        return jsonify({
            'message': 'Đơn thuê đã được tạo thành công!',
            'rental_id': new_rental.id,
            'customer': {'id': customer.id, 'name': customer.name, 'phone': customer.phone},
            'total_price': total_price,
            'books': book_details
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating rental: {str(e)}")
        return jsonify({'message': f'Lỗi khi tạo đơn thuê: {str(e)}'}), 500

# Trang quản lý đơn thuê
@rental_views.route('/manage_rentals')
@login_required
def manage_rentals():
    return render_template('manage_rentals.html')

# API lấy danh sách đơn thuê
@rental_views.route('/rentals', methods=['GET'])
@login_required
def get_all_rentals():
    try:
        rentals = Rental.query.join(Customer).filter(
            Rental.total_price > 0,
            Customer.is_deleted == False
        ).all()
        rental_list = []
        vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date = datetime.now(vn_timezone)
        late_fee_per_day = 1000  # Phí phạt: 1000 VNĐ/ngày

        for rental in rentals:
            if not RentalDetail.query.filter_by(rental_id=rental.id).first():
                continue

            customer = Customer.query.filter_by(id=rental.customer_id, is_deleted=False).first()
            if not customer:
                continue

            total_late_days = 0
            late_fee = 0
            if rental.status != 'completed':
                rental_details = RentalDetail.query.filter_by(rental_id=rental.id, is_returned=False).all()
                is_overdue = False
                for detail in rental_details:
                    return_due_date = detail.return_due_date
                    if return_due_date.tzinfo is None:
                        return_due_date = vn_timezone.localize(return_due_date)

                    if current_date > return_due_date:
                        is_overdue = True
                        days_overdue = (current_date - return_due_date).days
                        total_late_days += days_overdue * detail.rental_quantity
                        late_fee += days_overdue * late_fee_per_day * detail.rental_quantity

                if is_overdue and rental.status != 'overdue':
                    rental.status = 'overdue'
                    db.session.commit()

            rental_list.append({
                'id': rental.id,
                'customer_name': customer.name,
                'rental_date': rental.rental_date.strftime('%Y-%m-%d %H:%M:%S'),
                'return_date': rental.return_date.strftime('%Y-%m-%d %H:%M:%S') if rental.return_date else None,
                'status': rental.status,
                'total_price': rental.total_price,
                'late_days': total_late_days,
                'late_fee': late_fee
            })

        logger.debug(f"Retrieved {len(rental_list)} rentals")
        return jsonify(rental_list), 200
    except Exception as e:
        logger.error(f"Error retrieving rentals: {str(e)}")
        return jsonify({'message': f'Lỗi khi lấy danh sách đơn thuê: {str(e)}'}), 500

# API tìm đơn thuê theo số điện thoại
@rental_views.route('/rentals/search', methods=['GET'])
@login_required
def search_rentals():
    try:
        phone = request.args.get('phone')
        customer = Customer.query.filter_by(phone=phone, is_deleted=False).first()
        if not customer:
            logger.debug(f"No customer found for phone {phone}")
            return jsonify([]), 200

        rentals = Rental.query.filter_by(customer_id=customer.id).all()
        result = []
        vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date = datetime.now(vn_timezone)
        late_fee_per_day = 1000

        for rental in rentals:
            has_valid_details = RentalDetail.query.join(Book).filter(
                RentalDetail.rental_id == rental.id,
                Book.is_deleted == False
            ).first() is not None
            if not has_valid_details:
                continue

            total_late_days = 0
            late_fee = 0
            if rental.status != 'completed':
                rental_details = RentalDetail.query.filter_by(rental_id=rental.id, is_returned=False).all()
                is_overdue = False
                for detail in rental_details:
                    return_due_date = detail.return_due_date
                    if return_due_date.tzinfo is None:
                        return_due_date = vn_timezone.localize(return_due_date)

                    if current_date > return_due_date:
                        is_overdue = True
                        days_overdue = (current_date - return_due_date).days
                        total_late_days += days_overdue * detail.rental_quantity
                        late_fee += days_overdue * late_fee_per_day * detail.rental_quantity

                if is_overdue and rental.status != 'overdue':
                    rental.status = 'overdue'
                    db.session.commit()

            result.append({
                'id': rental.id,
                'customer_name': customer.name,
                'rental_date': rental.rental_date.strftime('%Y-%m-%d'),
                'status': rental.status,
                'total_price': rental.total_price,
                'late_days': total_late_days,
                'late_fee': late_fee
            })

        logger.debug(f"Found {len(result)} rentals for phone {phone}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error searching rentals: {str(e)}")
        return jsonify({'message': f'Lỗi khi tìm kiếm đơn thuê: {str(e)}'}), 500

# API hoàn tất đơn thuê
@rental_views.route('/rentals/<int:rental_id>/complete', methods=['POST'])
@login_required
def complete_rental(rental_id):
    try:
        rental = Rental.query.get(rental_id)
        if not rental:
            logger.warning(f"Rental ID {rental_id} not found")
            return jsonify({'message': 'Đơn thuê không tồn tại'}), 404
        if rental.status == 'completed':
            logger.warning(f"Rental ID {rental_id} already completed")
            return jsonify({'message': 'Đơn thuê đã hoàn tất, không thể cập nhật lại'}), 400
        if rental.status not in ['active', 'overdue']:
            logger.warning(f"Rental ID {rental_id} not in Active or Overdue state")
            return jsonify({'message': 'Đơn thuê không ở trạng thái Active hoặc Overdue'}), 400

        customer = Customer.query.filter_by(id=rental.customer_id, is_deleted=False).first()
        if not customer:
            logger.error(f"Customer ID {rental.customer_id} not found or deleted")
            return jsonify({'message': 'Khách hàng không tồn tại hoặc đã bị xóa'}), 400

        vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date = datetime.now(vn_timezone)
        late_fee_per_day = 1000
        total_late_fee = 0

        details = RentalDetail.query.filter_by(rental_id=rental.id).all()
        for detail in details:
            book = Book.query.filter_by(id=detail.book_id, is_deleted=False).first()
            if not book:
                db.session.rollback()
                logger.error(f"Book ID {detail.book_id} not found or deleted")
                return jsonify({'message': f'Sách với ID {detail.book_id} không tồn tại hoặc đã bị xóa'}), 400
            if detail.rental_quantity <= 0:
                db.session.rollback()
                logger.error(f"Invalid return quantity for book ID {detail.book_id}")
                return jsonify({'message': 'Số lượng sách trả lại không hợp lệ'}), 400

            return_due_date = detail.return_due_date
            if return_due_date.tzinfo is None:
                return_due_date = vn_timezone.localize(return_due_date)

            if not detail.is_returned and current_date > return_due_date:
                days_overdue = (current_date - return_due_date).days
                total_late_fee += days_overdue * late_fee_per_day * detail.rental_quantity

            book.quantity += detail.rental_quantity
            detail.is_returned = True
            detail.returned_date = current_date

        rental.status = 'completed'
        rental.return_date = current_date
        rental.total_price += total_late_fee

        db.session.commit()
        logger.info(f"Completed rental ID {rental_id} with late fee {total_late_fee}")
        return jsonify({
            'message': 'Đã hoàn tất đơn thuê và cập nhật kho sách',
            'late_fee': total_late_fee
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing rental ID {rental_id}: {str(e)}")
        return jsonify({'message': f'Lỗi server khi cập nhật đơn thuê: {str(e)}'}), 500

# API lấy chi tiết đơn thuê
@rental_views.route('/rentals/<int:rental_id>/details', methods=['GET'])
@login_required
def get_rental_details(rental_id):
    try:
        details = RentalDetail.query.join(Book).filter(
            RentalDetail.rental_id == rental_id,
            Book.is_deleted == False
        ).all()
        result = []
        vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date = datetime.now(vn_timezone)
        late_fee_per_day = 1000

        for detail in details:
            book = Book.query.filter_by(id=detail.book_id, is_deleted=False).first()
            if not book:
                continue

            return_due_date = detail.return_due_date
            if return_due_date.tzinfo is None:
                return_due_date = vn_timezone.localize(return_due_date)

            days_overdue = 0
            if not detail.is_returned and current_date > return_due_date:
                days_overdue = (current_date - return_due_date).days

            result.append({
                'book_title': book.title,
                'rental_quantity': detail.rental_quantity,
                'return_due_date': detail.return_due_date.strftime('%Y-%m-%d %H:%M:%S'),
                'returned_date': detail.returned_date.strftime('%Y-%m-%d %H:%M:%S') if detail.returned_date else None,
                'is_returned': detail.is_returned,
                'late_days': days_overdue,
                'late_fee': days_overdue * late_fee_per_day * detail.rental_quantity
            })

        logger.debug(f"Retrieved {len(result)} details for rental ID {rental_id}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error retrieving details for rental ID {rental_id}: {str(e)}")
        return jsonify({'message': f'Lỗi khi lấy chi tiết đơn thuê: {str(e)}'}), 500

# Hàm xóa các đơn thuê rỗng
def clean_empty_rentals():
    try:
        empty_rentals = Rental.query.filter_by(total_price=0).all()
        for rental in empty_rentals:
            details = RentalDetail.query.join(Book).filter(
                RentalDetail.rental_id == rental.id,
                Book.is_deleted == False
            ).first()
            if not details:
                db.session.delete(rental)
        db.session.commit()
        logger.info("Deleted empty rentals")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cleaning empty rentals: {str(e)}")

