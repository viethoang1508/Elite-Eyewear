from flask import Blueprint, jsonify, render_template, request, session, flash, redirect, url_for
import sqlite3
import random
from .utils import convert_currency_to_int

views = Blueprint("views", __name__)

sqldbname = 'Elite_Eyewear.db'

# Hàm tiện ích để lấy current_username
def get_current_username():
    return session['current_user']['name'] if 'current_user' in session else ""

def generate_random_numbers():
    return [random.randint(1, 12) for _ in range(4)]

@views.route('/')
def home():
    current_username = get_current_username()
    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM eyeglasses LIMIT 0, 4')
            featuresProduct = cursor.fetchall()
            cursor.execute('SELECT * FROM eyeglasses LIMIT 4, 10')
            latestProducts = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("views.home"))
    return render_template('home.html', featuresProduct=featuresProduct, latestProducts=latestProducts,
                           user_name=current_username)

@views.route('/cart', methods=['GET'])
def shopping_cart():
    current_username = get_current_username()
    current_cart = session.get('cart', [])
    return render_template('cart.html', cart=current_cart, user_name=current_username)

@views.route('/all_products')
def all_products():
    current_username = get_current_username()
    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM eyeglasses')
            all_products = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("views.home"))
    return render_template('all_products.html', all_products=all_products, user_name=current_username)

@views.route('/product_detail/<id>')
def product_detail(id):
    current_username = get_current_username()
    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM eyeglasses WHERE id = ?', (id,))
            product_detail = cursor.fetchone()
            if not product_detail:
                flash("Sản phẩm không tồn tại.", "error")
                return redirect(url_for("views.all_products"))
            random_numbers = generate_random_numbers()
            cursor.execute('SELECT * FROM eyeglasses WHERE id IN (?,?,?,?)',
                           (random_numbers[0], random_numbers[1], random_numbers[2], random_numbers[3]))
            related_products = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for("views.all_products"))
    return render_template('product_detail.html', product_detail=product_detail, related_products=related_products,
                           user_name=current_username)

@views.route('/about')
def about():
    current_username = get_current_username()
    return render_template('about.html', user_name=current_username)

@views.route('/contact', methods=['GET', 'POST'])
def contact():
    current_username = get_current_username()
    if request.method == 'POST':
        Name = request.form['Name']
        Tel = request.form['Tel']
        Email = request.form['Email']
        Message = request.form['message']
        try:
            with sqlite3.connect(sqldbname) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Contact (Name, Tel, Email, Messages) VALUES (?, ?, ?, ?)",
                               (Name, Tel, Email, Message))
                conn.commit()
            flash("Thank you for your feedback", "success")
            return redirect(url_for('views.contact'))
        except sqlite3.Error as e:
            flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
            return render_template('contact.html', user_name=current_username)
    return render_template('contact.html', user_name=current_username)

@views.route('/cart/add', methods=['POST'])
def addToCart():
    productId = request.form['product_id']
    try:
        quantity = int(request.form['quantity'])
        if quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0.")
    except (ValueError, KeyError) as e:
        flash(f"Lỗi: {str(e)}", "error")
        return redirect(url_for('views.product_detail', id=productId))

    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product, price, picture FROM eyeglasses WHERE id = ?", (productId,))
            product = cursor.fetchone()
            if not product:
                raise ValueError("Sản phẩm không tồn tại.")
    except (sqlite3.Error, ValueError) as e:
        flash(f"Lỗi: {str(e)}", "error")
        return redirect(url_for('views.product_detail', id=productId))

    product_detail = {
        "id": productId,
        "name": product[0],
        "price": product[1],
        "image": product[2],
        "quantity": quantity
    }
    cart = session.get('cart', [])
    found = False
    for item in cart:
        if item["id"] == productId:
            item["quantity"] += quantity
            found = True
            break
    if not found:
        cart.append(product_detail)
    session["cart"] = cart
    flash('Item added successfully!', 'success')
    return redirect(url_for('views.product_detail', id=productId))

@views.route('/cart/update', methods=['POST'])
def CartUpdate():
    cart = session.get('cart', [])
    new_cart = []
    for row in cart:
        productId = int(row['id'])
        if f'quantity-{productId}' in request.form:
            try:
                quantity = int(request.form[f'quantity-{productId}'])
                if quantity < 0:
                    raise ValueError("Số lượng không thể âm.")
                if quantity == 0 or f'delete-{productId}' in request.form:
                    continue
                row['quantity'] = quantity
            except ValueError as e:
                flash(f"Lỗi: {str(e)}", "error")
                return redirect(url_for('views.shopping_cart'))
        new_cart.append(row)
    session['cart'] = new_cart
    return redirect(url_for('views.shopping_cart'))

@views.route('/proceed_cart', methods=['POST'])
def proceed_cart():
    if 'current_user' not in session:
        flash("Bạn cần đăng nhập để tiếp tục.", "error")
        return redirect(url_for("auth.login"))

    if 'cart' not in session or not session['cart']:
        flash("Giỏ hàng trống. Hãy thêm sản phẩm!", "info")
        return redirect(url_for("views.all_products"))

    return render_template('checkout.html', cart=session['cart'], user_name=session['current_user']['name'])

@views.route('/process-checkout', methods=['POST'])
def process_checkout():
    if 'current_user' not in session:
        flash("Bạn cần đăng nhập để tiếp tục.", "error")
        return redirect(url_for("auth.login"))

    if 'cart' not in session or not session['cart']:
        flash("Giỏ hàng trống.", "error")
        return redirect(url_for("views.shopping_cart"))

    # Lấy thông tin từ form
    name = request.form['name']
    address = request.form['address']
    phone = request.form['phone']
    payment_method = request.form['payment_method']

    # Lấy thông tin người dùng từ session
    user_id = session['current_user']['id']
    user_email = session['current_user']['email']
    current_cart = session.get("cart", [])

    try:
        with sqlite3.connect(sqldbname) as conn:
            conn.execute('PRAGMA busy_timeout = 30000')  # Tăng thời gian chờ lên 30 giây
            cur = conn.cursor()
            status = 1  # Đơn hàng đang chờ xử lý
            cur.execute(
                'INSERT INTO "order" (user_id, user_email, status) VALUES (?, ?, ?)',
                (user_id, user_email, status)
            )
            order_id = cur.lastrowid  # Lấy ID của đơn hàng vừa tạo

            # Lưu chi tiết đơn hàng vào bảng `order_details`
            for product in current_cart:
                product_id = product['id']
                price = product['price']
                quantity = product['quantity']
                price_value = convert_currency_to_int(price) if isinstance(price, str) else price
                cur.execute(
                    'INSERT INTO "order_details" (order_id, product_id, price, quantity, shipping_name, shipping_address, shipping_phone, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (order_id, product_id, price_value, quantity, name, address, phone, payment_method)
                )

            conn.commit()

    except sqlite3.OperationalError as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}. Vui lòng thử lại sau.", "error")
        return redirect(url_for("views.shopping_cart"))

    # Xóa giỏ hàng sau khi đặt hàng thành công
    session.pop('cart', None)

    # Hiển thị thông báo thành công
    flash(f"Đơn hàng của bạn đã được đặt thành công! Mã đơn hàng: {order_id}", "success")
    return redirect(url_for("views.account"))

@views.route('/account/', methods=['GET'])
def account():
    user_orders = []
    current_username = get_current_username()
    user_id = session.get('current_user', {}).get('id')
    if user_id:
        try:
            with sqlite3.connect(sqldbname) as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM "order" WHERE user_id = ?', (user_id,))
                user_orders = cur.fetchall()
        except sqlite3.Error as e:
            flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
            return redirect(url_for("auth.login"))
        return render_template('account.html', orders=user_orders, user_name=current_username)
    flash("User not logged in")
    return redirect(url_for("auth.login"))

@views.route('/order/', defaults={'order_id': None}, methods=['GET'])
@views.route('/order/<int:order_id>/', methods=['GET'])
def order(order_id):
    current_username = get_current_username()
    user_id = session.get('current_user', {}).get('id')
    if user_id:
        try:
            with sqlite3.connect(sqldbname) as conn:
                cur = conn.cursor()
                if order_id is not None:
                    cur.execute('SELECT * FROM "order" WHERE id = ? AND user_id = ?', (order_id, user_id))
                    order = cur.fetchone()
                    if not order:
                        flash("Đơn hàng không tồn tại hoặc không thuộc về bạn.", "error")
                        return redirect(url_for("views.account"))
                    cur.execute(
                        'SELECT product_id, product, order_details.price, quantity FROM order_details INNER JOIN eyeglasses ON eyeglasses.id = order_details.product_id WHERE order_id = ?',
                        (order_id,)
                    )
                    order_details = cur.fetchall()
                    return render_template('orders.html', order=order, order_details=order_details,
                                           user_name=current_username)
                else:
                    cur.execute('SELECT * FROM "order" WHERE user_id = ?', (user_id,))
                    user_orders = cur.fetchall()
                    if not user_orders:
                        user_orders = None
                    return render_template('account.html', orders=user_orders, user_name=current_username)
        except sqlite3.Error as e:
            flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
            return redirect(url_for("views.account"))
    flash("User not logged in")
    return redirect(url_for("auth.login"))

@views.route('/all-product', methods=['GET'])
def get_all_products():
    filter_by = request.args.get('filter')
    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            match filter_by:
                case "Default Sort":
                    sqlcommand = "SELECT * FROM eyeglasses"
                case "Sort By Price":
                    sqlcommand = "SELECT * FROM eyeglasses ORDER BY CAST(REPLACE(REPLACE(price, '$', ''), '.', '') AS INT)"
                case "Sort By Price DESC":
                    sqlcommand = "SELECT * FROM eyeglasses ORDER BY CAST(REPLACE(REPLACE(price, '$', ''), '.', '') AS INT) DESC"
                case "Sort By Rating":
                    sqlcommand = "SELECT * FROM eyeglasses ORDER BY rating DESC"
                case "Sort By Brand":
                    sqlcommand = "SELECT * FROM eyeglasses ORDER BY brand"
                case _:
                    sqlcommand = "SELECT * FROM eyeglasses"
            cursor.execute(sqlcommand)
            data = cursor.fetchall()
    except sqlite3.Error as e:
        return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
    return jsonify(data)

@views.route('/search', methods=['POST'])
def search():
    current_username = get_current_username()
    search_text = request.form['searchInput']
    if search_text == "":
        flash("You must add some text", "error")
        return render_template('all_products.html', search_text=search_text, all_products=[],
                               user_name=current_username)

    try:
        with sqlite3.connect(sqldbname) as conn:
            cursor = conn.cursor()
            sqlcommand = "SELECT * FROM eyeglasses WHERE product LIKE ?"
            cursor.execute(sqlcommand, ('%' + search_text + '%',))
            data = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return render_template('all_products.html', search_text=search_text, all_products=[],
                               user_name=current_username)
    flash(search_text, 'success')
    return render_template('all_products.html', search_text=search_text, all_products=data, user_name=current_username)