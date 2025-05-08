from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User
import bcrypt
from flask_login import login_required, login_user, current_user, logout_user

admin_views = Blueprint('admin_views', __name__)

#hàm kiểm tra quyền admin
def is_admin():
    #return session.get('role') == 'admin'
    return current_user.is_authenticated and current_user.role == 'admin'

# Route khởi tạo tài khoản admin mặc định
@admin_views.route('/admin/init', methods=['GET'])
@login_required
def init_admin():
    if not is_admin():
        flash('Bạn không có quyền thực hiện thao tác này.')
        return redirect(url_for('admin_views.login'))
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        hashed_password = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(
            username='admin',
            password=hashed_password,
            name='Admin Nhi',
            email='admin@bookstart.com',
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        flash('Tạo tài khoản admin mặc định thành công: username=admin, password=admin.')
    else:
        flash('Tài khoản admin đã tồn tại.')
    return redirect(url_for('admin_views.admin_dashboard'))

# Route đăng nhập
@admin_views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')) and user.is_active:
            #session['user_id'] = user.id
            #session['role'] = user.role
            login_user(user, remember=True)
            if user.role == 'admin':
                return redirect(url_for('admin_views.admin_dashboard'))
            return redirect(url_for('admin_views.staff_dashboard'))
        flash('Tên đăng nhập hoặc mật khẩu không đúng, hoặc tài khoản đã bị vô hiệu hóa.')
    return render_template('login.html')

# Route đăng xuất
@admin_views.route('/logout')
def logout():
    #session.pop('user_id', None)
    #session.pop('role', None)
    logout_user()
    return redirect(url_for('admin_views.login'))

# Route dashboard admin
@admin_views.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.')
        return redirect(url_for('admin_views.login'))
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

# Route dashboard nhân viên
@admin_views.route('/staff')
@login_required
def staff_dashboard():
    #if 'user_id' not in session:
    #    flash('Vui lòng đăng nhập.')
    #    return redirect(url_for('admin_views.login'))
    return render_template('staff_dashboard.html')

# Route tạo tài khoản nhân viên
@admin_views.route('/admin/create_user', methods=['GET', 'POST'])
def create_user():
    if not is_admin():
        flash('Bạn không có quyền thực hiện thao tác này.')
        return redirect(url_for('admin_views.login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.')
            return render_template('create_user.html')
        if User.query.filter_by(email=email).first():
            flash('Email đã tồn tại.')
            return render_template('create_user.html')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=username, password=hashed_password, name=name, email=email, role='staff', is_active=True)
        db.session.add(new_user)
        db.session.commit()
        flash('Tạo tài khoản thành công.')
        return redirect(url_for('admin_views.admin_dashboard'))
    return render_template('create_user.html')

# Route sửa thông tin nhân viên
@admin_views.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    if not is_admin():
        flash('Bạn không có quyền thực hiện thao tác này.')
        return redirect(url_for('admin_views.login'))
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter(User.username == username, User.id != id).first():
            flash('Tên đăng nhập đã tồn tại.')
            return render_template('edit_user.html', user=user)
        if User.query.filter(User.email == email, User.id != id).first():
            flash('Email đã tồn tại.')
            return render_template('edit_user.html', user=user)
        user.username = username
        user.name = name
        user.email = email
        if password:
            user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        flash('Cập nhật thông tin thành công.')
        return redirect(url_for('admin_views.admin_dashboard'))
    return render_template('edit_user.html', user=user)

# Route vô hiệu hóa tài khoản nhân viên
@admin_views.route('/admin/deactivate_user/<int:id>')
def deactivate_user(id):
    if not is_admin():
        flash('Bạn không có quyền thực hiện thao tác này.')
        return redirect(url_for('admin_views.login'))
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('Không thể vô hiệu hóa tài khoản admin.')
        return redirect(url_for('admin_views.admin_dashboard'))
    user.is_active = False
    db.session.commit()
    flash('Vô hiệu hóa tài khoản thành công.')
    return redirect(url_for('admin_views.admin_dashboard'))