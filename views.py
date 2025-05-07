from flask import Blueprint, request, jsonify, render_template
from models import db, Book, Rental, RentalDetail
from unidecode import unidecode
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Khởi tạo Blueprint
views = Blueprint("views", __name__)

#### QUẢN LÝ SÁCH ####

# API: Lấy danh sách sách
@views.route("/books", methods=["GET"])
def get_books():
    try:
        books = Book.query.filter_by(is_deleted=False).all()
        book_list = [{
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "quantity": b.quantity,
            "rental_price": b.rental_price
        } for b in books]
        logger.info(f"Retrieved {len(book_list)} books")
        return jsonify(book_list), 200
    except Exception as e:
        logger.error(f"Error retrieving books: {str(e)}")
        return jsonify({"message": f"Lỗi khi lấy danh sách sách: {str(e)}"}), 500

# API: Thêm sách mới
@views.route("/add_book", methods=["POST"])
def add_book():
    try:
        data = request.json
        if not data or 'title' not in data or 'author' not in data or 'quantity' not in data or 'rental_price' not in data:
            logger.warning("Invalid book data provided")
            return jsonify({"message": "Vui lòng cung cấp đầy đủ tiêu đề, tác giả, số lượng và giá thuê!"}), 400

        try:
            quantity = int(data['quantity'])
            rental_price = float(data['rental_price'])
        except (ValueError, TypeError):
            logger.warning("Invalid quantity or rental price format")
            return jsonify({"message": "Số lượng và giá thuê phải là số hợp lệ!"}), 400

        if quantity < 0:
            logger.warning("Negative quantity provided")
            return jsonify({"message": "Số lượng sách không thể âm!"}), 400
        if rental_price <= 0:
            logger.warning("Non-positive rental price provided")
            return jsonify({"message": "Giá thuê phải lớn hơn 0!"}), 400

        existing_book = Book.query.filter_by(title=data['title'], is_deleted=False).first()
        if existing_book:
            logger.warning(f"Book with title {data['title']} already exists")
            return jsonify({"message": "Sách với tiêu đề này đã tồn tại!"}), 400

        new_book = Book(
            title=data['title'],
            author=data['author'],
            quantity=quantity,
            rental_price=rental_price,
            is_deleted=False
        )
        db.session.add(new_book)
        db.session.commit()
        logger.info(f"Created book ID {new_book.id}")
        return jsonify({"message": "Sách được thêm thành công", "id": new_book.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating book: {str(e)}")
        return jsonify({"message": f"Lỗi khi thêm sách: {str(e)}"}), 500

# API: Tìm kiếm sách theo tiêu đề hoặc tác giả
@views.route("/search_books", methods=["GET"])
def search_books():
    try:
        query = request.args.get("query", "").strip()
        if not query:
            logger.warning("Empty search query provided")
            return jsonify({"message": "Vui lòng cung cấp từ khóa tìm kiếm!"}), 400

        books = Book.query.filter(
            (Book.title.ilike(f"%{query}%")) | (Book.author.ilike(f"%{query}%")),
            Book.is_deleted == False
        ).all()

        if not books:
            logger.info(f"No books found for query: {query}")
            return jsonify({"message": "Không tìm thấy sách nào!"}), 404

        book_list = [{
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "quantity": b.quantity,
            "rental_price": b.rental_price
        } for b in books]
        logger.info(f"Found {len(book_list)} books for query: {query}")
        return jsonify(book_list), 200
    except Exception as e:
        logger.error(f"Error searching books: {str(e)}")
        return jsonify({"message": f"Lỗi khi tìm kiếm sách: {str(e)}"}), 500

# API: Cập nhật thông tin sách
@views.route("/update_book/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    try:
        book = Book.query.filter_by(id=book_id, is_deleted=False).first()
        if not book:
            logger.warning(f"Book ID {book_id} not found or deleted")
            return jsonify({"message": "Sách không tồn tại hoặc đã bị xóa!"}), 404

        data = request.json
        if not data:
            logger.warning("No update data provided")
            return jsonify({"message": "Không có dữ liệu cập nhật!"}), 400

        try:
            new_quantity = int(data.get("quantity", book.quantity))
            new_rental_price = float(data.get("rental_price", book.rental_price))
        except (ValueError, TypeError):
            logger.warning("Invalid quantity or rental price format")
            return jsonify({"message": "Số lượng và giá thuê phải là số hợp lệ!"}), 400

        new_title = data.get("title", book.title)
        if new_title != book.title:
            existing_book = Book.query.filter_by(title=new_title, is_deleted=False).first()
            if existing_book:
                logger.warning(f"Book with title {new_title} already exists")
                return jsonify({"message": "Sách với tiêu đề này đã tồn tại!"}), 400

        if new_quantity < 0:
            logger.warning("Negative quantity provided")
            return jsonify({"message": "Số lượng sách không thể âm!"}), 400
        if new_rental_price <= 0:
            logger.warning("Non-positive rental price provided")
            return jsonify({"message": "Giá thuê phải lớn hơn 0!"}), 400

        book.title = new_title
        book.author = data.get("author", book.author)
        book.quantity = new_quantity
        book.rental_price = new_rental_price
        db.session.commit()
        logger.info(f"Updated book ID {book_id}")
        return jsonify({"message": "Thông tin sách đã được cập nhật!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating book ID {book_id}: {str(e)}")
        return jsonify({"message": f"Lỗi khi cập nhật sách: {str(e)}"}), 500

# API: Xóa mềm sách
@views.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            logger.warning(f"Book ID {book_id} not found")
            return jsonify({"message": "Sách không tồn tại!"}), 404

        if book.is_deleted:
            logger.warning(f"Book ID {book_id} already deleted")
            return jsonify({"message": "Sách đã được xóa trước đó!"}), 400

        # Kiểm tra xem sách có trong đơn thuê active hoặc overdue
        incomplete_rentals = RentalDetail.query.join(Rental).filter(
            RentalDetail.book_id == book_id,
            Rental.status.in_(['active', 'overdue'])
        ).count()
        if incomplete_rentals > 0:
            logger.warning(f"Book ID {book_id} is in {incomplete_rentals} active or overdue rentals")
            return jsonify({"message": "Không thể xóa sách vì còn trong đơn thuê active hoặc quá hạn!"}), 400

        # Xóa mềm
        book.is_deleted = True
        db.session.commit()
        logger.info(f"Deleted book ID {book_id}")
        return jsonify({"message": "Sách đã được xóa thành công!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting book ID {book_id}: {str(e)}")
        return jsonify({"message": f"Lỗi khi xóa sách: {str(e)}"}), 500

# Trang chính
@views.route("/")
def index():
    return render_template("index.html")