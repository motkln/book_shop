import flask
from flask import render_template, request, Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from db.models import User, Review, Book, Cartitem, Orderitem, Order
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
from db.database import session_scope, get_books_slice

main_blueprint = Blueprint('main', __name__)


@main_blueprint.route('/')
def main():
    with session_scope() as session:
        find_books = session.query(Book).order_by(Book.rating.desc()).limit(3).all()
        top_books = [
            {"id": book.id,
             "title": book.title,
             "author": book.author,
             "price": book.price,
             "genre": book.genre,
             "cover": book.cover,
             "description": book.description,
             "rating": book.rating,
             "year": book.year}
            for book in find_books
        ]
    return render_template('index.html', name=current_user.name if current_user.is_authenticated else None,
                           top_books=top_books)


@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        with session_scope() as session:
            email = request.form.get("email")
            password = request.form.get("password")
            user = session.query(User).filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("main.main"))  # <-- редирект на главную
            else:
                flash("Неверный email или пароль", "error")
                return render_template("login.html")
    return render_template('login.html')


@main_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        code = str(random.randint(1000, 9999))  # имитация SMS-кода
        with session_scope() as session:
            exist_user = session.query(User).filter_by(email=email).first()
            if not exist_user:
                user = User(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash(password),
                    sms_code=code
                )
                session.add(user)
                session.flush()

                user_id = user.id
                flask.session["pending_user_id"] = user_id
                flash(f"Ваш код подтверждения (имитация SMS): {code}", "info")
                return redirect(url_for("main.confirm_sms"))
            else:
                flash("Данный пользоватлеь уже существует", "error")
    return render_template("register.html")


@main_blueprint.route("/confirm_sms", methods=["GET", "POST"])
def confirm_sms():
    user_id = flask.session.get("pending_user_id")
    if not user_id:
        return redirect(url_for("main.register"))

    if request.method == "POST":
        entered_code = request.form.get("code")

        with session_scope() as session:
            user = session.get(User, user_id)
            if user and user.sms_code == entered_code:
                user.is_confirmed = True
                user.sms_code = None
                flash("Регистрация подтверждена! Теперь можно войти.", "success")
                return redirect(url_for("main.login"))
            else:
                flash("Неверный код, попробуйте снова.", "danger")

    return render_template("confirm.html")

@main_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.main'))


@main_blueprint.route('/catalog/')
@main_blueprint.route('/catalog/<current_genre>')
def show_catalog(current_genre=None):
    start_index = int(request.args.get("start_index", 0))
    window = int(request.args.get("window", 4))
    with session_scope() as session:
        all_genres = session.query(Book.genre).distinct().all()
        genres = [genre[0] for genre in all_genres]

        if current_genre:
            total = session.query(Book).filter(Book.genre == current_genre).count()
            books = get_books_slice(current_genre, start_index, window)
            return render_template('catalog.html', genres=genres, books=books,
                                   start_index=start_index, window=window, current_genre=current_genre, total=total)

        return render_template('catalog.html', genres=genres)


@main_blueprint.route('/books/<int:id>', methods=['POST', 'GET'])
def show_books(id):
    if request.method == 'GET':
        with session_scope() as session:
            book = session.get(Book, id)
            book_data = {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "price": book.price,
                "genre": book.genre,
                "cover": book.cover,
                "description": book.description,
                "rating": book.rating,
                "year": book.year
            }
            reviews = session.query(Review).filter_by(book_id=id).all()
            reviews_data = [
                {
                    "id": r.id,
                    "description": r.description,
                    "rating": r.rating,
                    "user_name": r.user.name
                } for r in reviews
            ]

            return render_template('book_detail.html', book=book_data, reviews=reviews_data)

    if request.method == 'POST':
        with session_scope() as session:
            rating = int(request.form.get('rating'))
            review_text = request.form.get('text')
            review = Review(
                description=review_text,
                user_id=current_user.id,
                book_id=id,
                rating=rating)
            session.add(review)
        return redirect(url_for('main.show_books', id=id))


@main_blueprint.route('/add_to_cart/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_cart(id):
    if request.method == 'POST':

        with session_scope() as session:
            cart_item = session.query(Cartitem).filter_by(user_id=current_user.id, book_id=id).first()

            if cart_item:
                cart_item.quantity += 1
            else:
                new_item = Cartitem(
                    user_id=current_user.id,
                    book_id=id,
                    quantity=1)
                session.add(new_item)

            flash('Предмет добавлен в корзину', 'success')
    return redirect(url_for('main.show_books', id=id))


@main_blueprint.route('/cart')
@login_required
def cart():
    with session_scope() as session:
        all_items = session.query(Cartitem).filter_by(user_id=current_user.id).all()
        items = [
            {
                "id": ci.id,
                "book_id": ci.book.id,
                "title": ci.book.title,
                "cover": ci.book.cover,
                "author": ci.book.author,
                "price": ci.book.price,
                "quantity": ci.quantity,
                "user_name": ci.user.name,
            }
            for ci in all_items]

        total = sum(ci['price'] * ci['quantity'] for ci in items)

    return render_template('cart.html', items=items, total=total)


@main_blueprint.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    quantity = int(request.form.get('quantity', 1))

    with session_scope() as session:
        cart_item = session.query(Cartitem).filter_by(id=item_id, user_id=current_user.id).first()
        if cart_item:
            cart_item.quantity = quantity
            session.add(cart_item)

    return redirect(url_for('main.cart'))


@main_blueprint.route('/checkout', methods=['POST', 'GET'])
@login_required
def checkout():
    if request.method == 'POST':
        address = request.form.get('address')
        if address:
            new_order = Order(user_id=current_user.id, address=address)
        else:
            new_order = Order(user_id=current_user.id)
        with session_scope() as session:
            session.add(new_order)
            session.flush()
            cart_items = session.query(Cartitem).filter_by(user_id=current_user.id).all()
            if cart_items:
                for ci in cart_items:
                    order_item = Orderitem(
                        order_id=new_order.id,
                        book_id=ci.book_id,
                        quantity=ci.quantity
                    )
                    session.add(order_item)

            session.query(Cartitem).filter_by(user_id=current_user.id).delete()
            return redirect(url_for('main.orders'))
    return render_template('checkout.html')


@main_blueprint.route("/orders", methods=['POST', 'GET'])
@login_required
def orders():
    if request.method == "GET":
        with session_scope() as session:
            all_orders = session.query(Order).filter_by(user_id=current_user.id)
            orders = []
            for ord in all_orders:
                items_list = [
                    {
                        'book_id': item.book.id,
                        'title': item.book.title,
                        'price': item.book.price,
                        'quantity': item.quantity,
                        'total': item.quantity * item.book.price
                    }
                    for item in ord.orderitems
                ]
                order_total = sum(it['total'] for it in items_list)

                orders.append({
                    'id': ord.id,
                    'date': ord.date,
                    'status': ord.status,
                    'address': ord.address,
                    'items': items_list,
                    'total': order_total  # <-- добавляем сюда
                })

            all_status = {0: 'Оформлен', 1: 'Сборка', 2: 'В пути', 3: 'Доставлен'}
            return render_template('orders.html', orders=orders, current_status=all_status)
    return redirect(url_for('main.orders'))


@main_blueprint.route('/detele_from_cart/<int:item_id>', methods=["POST"])
def remove_from_cart(item_id):
    with session_scope() as session:
        deleted_object = session.get(Cartitem, item_id)
        if deleted_object:
            session.delete(deleted_object)
    return redirect(url_for('main.cart'))
