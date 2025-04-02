from flask import Blueprint, render_template, request, session, flash, redirect, url_for
import sqlite3
from functools import wraps
from .utils import convert_currency_to_int
from flask_mail import Message
from flask import current_app

admin = Blueprint("admin", __name__)

sqldbname = 'Elite_Eyewear.db'

# Decorator để kiểm tra quyền admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'current_user' not in session or session['current_user'].get('admin') != 1:
            flash("Bạn cần quyền quản trị viên để truy cập trang này.", "error")
            return redirect(url_for("views.home"))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@admin_required
def index():
    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            sqlcommand = "SELECT * FROM eyeglasses"
            cursor.execute(sqlcommand)
            storages = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("views.home"))
    return render_template('admin/dashboard.html', storages=storages)

@admin.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        product = request.form['Product']
        brand = request.form['Brand']
        rating = request.form['Rating']
        model = request.form['Model']
        picture = request.form['Picture']
        price = request.form['Price']
        details = request.form['Details']

        # Kiểm tra dữ liệu đầu vào (validation)
        try:
            rating = float(rating)  # Đảm bảo rating là số
            if rating < 0 or rating > 5:
                raise ValueError("Rating phải nằm trong khoảng từ 0 đến 5.")
        except ValueError as e:
            flash(f"Lỗi: {str(e)}", "error")
            return render_template('admin/add.html')

        try:
            with sqlite3.connect(sqldbname) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO eyeglasses (product, brand, rating, model, picture, price, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (product, brand, rating, model, picture, price, details)
                )
                conn.commit()
            flash("Bạn đã thêm sản phẩm thành công!", "success")
            return redirect(url_for('admin.index'))
        except sqlite3.Error as e:
            flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
            return render_template('admin/add.html')

    return render_template('admin/add.html')

@admin.route('/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM eyeglasses WHERE id = ?", (id,))
            storage = cursor.fetchone()
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("admin.index"))

    if not storage:
        flash("Sản phẩm không tồn tại.", "error")
        return redirect(url_for("admin.index"))

    if request.method == 'POST':
        product = request.form['Product']
        brand = request.form['Brand']
        rating = request.form['Rating']
        model = request.form['Model']
        picture = request.form['Picture']
        price = request.form['Price']
        details = request.form['Details']

        # Kiểm tra dữ liệu đầu vào (validation)
        try:
            rating = float(rating)  # Đảm bảo rating là số
            if rating < 0 or rating > 5:
                raise ValueError("Rating phải nằm trong khoảng từ 0 đến 5.")
        except ValueError as e:
            flash(f"Lỗi: {str(e)}", "error")
            return render_template("admin/edit.html", storage=storage)

        try:
            with sqlite3.connect(sqldbname) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE eyeglasses SET product = ?, brand = ?, rating = ?, model = ?, picture = ?, price = ?, details = ? WHERE id = ?",
                    (product, brand, rating, model, picture, price, details, id)
                )
                conn.commit()
            flash("Sản phẩm đã được cập nhật thành công!", "success")
            return redirect(url_for("admin.index"))
        except sqlite3.Error as e:
            flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
            return render_template("admin/edit.html", storage=storage)

    return render_template("admin/edit.html", storage=storage)

@admin.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete(id):
    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM eyeglasses WHERE id = ?", (id,))
            conn.commit()
        flash("Bạn đã xóa sản phẩm thành công!", "success")
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
    return redirect(url_for('admin.index'))

@admin.route('/orders', methods=['GET'])
@admin_required
def admin_orders():
    try:
        with sqlite3.connect(sqldbname) as conn:
            cur = conn.cursor()
            # Lấy tất cả đơn hàng từ bảng `order`
            cur.execute('SELECT * FROM "order"')
            orders = cur.fetchall()
            # Lấy thông tin chi tiết đơn hàng từ bảng `order_details`
            order_details = {}
            for order in orders:
                order_id = order[0]  # Cột `id` của bảng `order`
                cur.execute(
                    'SELECT product_id, product, order_details.price, quantity, shipping_name, shipping_address, shipping_phone, payment_method FROM order_details INNER JOIN eyeglasses ON eyeglasses.id = order_details.product_id WHERE order_id = ?',
                    (order_id,)
                )
                details = cur.fetchall()
                # Chuyển đổi price (detail[2]) từ chuỗi sang số
                converted_details = []
                for detail in details:
                    detail_list = list(detail)
                    detail_list[2] = convert_currency_to_int(detail_list[2]) if isinstance(detail_list[2], str) else int(detail_list[2])
                    converted_details.append(tuple(detail_list))
                order_details[order_id] = converted_details
            # Lọc các đơn hàng có chi tiết đơn hàng
            orders_with_details = [order for order in orders if order_details[order[0]]]
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("views.home"))

    return render_template('admin/admin_orders.html', orders=orders_with_details, order_details=order_details)  # Xóa storages

@admin.route('/contacts', methods=['GET'])
@admin_required
def admin_contacts():
    try:
        with sqlite3.connect(sqldbname) as conn:
            cur = conn.cursor()
            # Lấy tất cả liên hệ từ bảng `Contact`
            cur.execute('SELECT * FROM "Contact"')
            contacts = cur.fetchall()
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("views.home"))

    return render_template('admin/admin_contacts.html', contacts=contacts)  # Xóa storages

@admin.route('/reply/<int:contact_id>', methods=['GET', 'POST'])
@admin_required
def reply_contact(contact_id):
    # Sử dụng current_app để truy cập mail
    mail = current_app.mail

    try:
        with sqlite3.connect(sqldbname) as conn:
            cur = conn.cursor()
            # Lấy thông tin liên hệ
            cur.execute('SELECT * FROM "Contact" WHERE id = ?', (contact_id,))
            contact = cur.fetchone()
            if not contact:
                flash("Liên hệ không tồn tại.", "error")
                return redirect(url_for("admin.admin_contacts"))
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("admin.admin_contacts"))

    if request.method == 'POST':
        # Lấy nội dung phản hồi từ form
        subject = request.form['subject']
        body = request.form['body']
        recipient = contact[3]  # Email của khách hàng

        # Gửi email
        try:
            msg = Message(subject=subject, recipients=[recipient], body=body)
            mail.send(msg)

            # Cập nhật trạng thái thành "Đã phản hồi"
            with sqlite3.connect(sqldbname) as conn:
                cur = conn.cursor()
                cur.execute('UPDATE "Contact" SET status = 1 WHERE id = ?', (contact_id,))
                conn.commit()

            flash("Phản hồi đã được gửi thành công!", "success")
            return redirect(url_for("admin.admin_contacts"))
        except Exception as e:
            flash(f"Lỗi khi gửi email: {str(e)}", "error")
            return render_template('admin/reply_contact.html', contact=contact)

    return render_template('admin/reply_contact.html', contact=contact)