from flask import Blueprint, request, jsonify, render_template
from models import db, Book
from unidecode import unidecode

# Khởi tạo Blueprint
views = Blueprint("views", __name__)


#### QUẢN LÝ SÁCH ####

# API: Lấy danh sách sách
@views.route("/books", methods=["GET"])
def get_books():
    books = Book.query.all()
    book_list = [{"id": b.id, "title": b.title, "author": b.author, "quantity": b.quantity, "rental_price": b.rental_price} for b in books]
    return jsonify(book_list)



# API: Thêm sách mới
@views.route("/add_book", methods=["POST"])
def add_book():
    data = request.json
    new_book = Book(title=data['title'], author=data['author'], quantity=data['quantity'], rental_price=data['rental_price'])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"message": "Sách được thêm thành công"}), 201


# API: Tìm kiếm sách theo tiêu đề hoặc tác giả
@views.route("/search_books", methods=["GET"])
def search_books():
    query = request.args.get("query", "").strip()

    print(f"Tìm kiếm cho: '{query}'")

    if not query:
        return jsonify({"message": "Please provide a search query"}), 400

    books = Book.query.filter(
        (Book.title.ilike(f"%{query}%")) | (Book.author.ilike(f"%{query}%"))    # Tìm theo cả tác giả, và tên sách
    ).all()

    if not books:
        return jsonify({"message": "No books found"}), 404

    book_list = [{"id": b.id, "title": b.title, "author": b.author, "quantity": b.quantity, "rental_price": b.rental_price} for b in books]
    return jsonify(book_list)


# API: Cập nhật thông tin sách
@views.route("/update_book/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"message": "Book not found"}), 404

    data = request.json
    book.title = data.get("title", book.title)
    book.author = data.get("author", book.author)
    book.quantity = data.get("quantity", book.quantity)
    book.rental_price = data.get("rental_price", book.rental_price)

    db.session.commit()
    return jsonify({"message": "Book updated successfully"})

# API: Xóa sách
@views.route("/delete_book/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"message": "Book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted successfully"})




# Trang chính
@views.route("/")
def index():
    return render_template("index.html")



