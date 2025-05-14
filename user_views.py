from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash

user_views = Blueprint('user_views', __name__)

# Chỉ admin mới truy cập được các route này
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'message': 'Chỉ admin mới có quyền truy cập!'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Trang quản lý nhân viên
@user_views.route('/manage_users')
@admin_required
def manage_users():
    return render_template('manage_users.html')

# API lấy danh sách nhân viên
@user_views.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'is_admin': u.is_admin
    } for u in users])

# API thêm nhân viên mới
@user_views.route('/add_user', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Vui lòng cung cấp tên đăng nhập và mật khẩu!'}), 400

    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'message': 'Tên đăng nhập đã tồn tại!'}), 400

    new_user = User(
        username=data['username'],
        password=generate_password_hash(data['password']),
        is_admin=data.get('is_admin', False)
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            'message': 'Nhân viên được thêm thành công!',
            'id': new_user.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi thêm nhân viên: {str(e)}'}), 500

# API cập nhật thông tin nhân viên
@user_views.route('/update_user/<int:id>', methods=['PUT'])
@admin_required
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Nhân viên không tồn tại!'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'Không có dữ liệu cập nhật!'}), 400

    if 'username' in data and data['username'] != user.username:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'message': 'Tên đăng nhập đã tồn tại!'}), 400
        user.username = data['username']

    if 'password' in data:
        user.password = generate_password_hash(data['password'])

    if 'is_admin' in data:
        user.is_admin = data['is_admin']

    try:
        db.session.commit()
        return jsonify({'message': 'Thông tin nhân viên đã được cập nhật!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật nhân viên: {str(e)}'}), 500

# API xóa nhân viên
@user_views.route('/users/<int:id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    if id == current_user.id:
        return jsonify({'message': 'Không thể xóa tài khoản của chính bạn!'}), 400

    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Nhân viên không tồn tại!'}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Nhân viên đã được xóa thành công!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa nhân viên: {str(e)}'}), 500