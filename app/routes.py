from app import app, session, request, db
from datetime import datetime
import sqlite3

from app.models import User, Product, ProductOrder, Order, OrderStatus

from config import SERVICE_INFO, ORDER_STATUS_EXPIRATION

@app.route('/')
def index():
    return "Welcome to the Pizza World!"


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Checking if user is authorized and authorizing if not (as a random user)
    req.args: {
        # login: String,
        # pass: String
    }
    :return:
    {
        user: User,
        error: 0,  # 2 - DB error
    }
    """

    result = {
        'error': 0,
        'user': None
    }
    if 'user_id' in session:
        result['user'] = {
            'id': session['user_id'],
            'name': session['user_name'],
            'phone': session['user_phone'],
            'address': session['user_address'],
        }
    else:
        user = None
        if request.get_json() is not None \
                and request.get_json().get('user_id') is not None:
            user = User.load_user(int(request.get_json().get('user_id')))

        if user is None:
            try:
                user = User.load_random_user()
            except Exception as ex:
                result['error'] = 2
                # or raise further maybe
                return result

        if user is not None:
            result['user'] = {
                'id': user.id,
                'name': user.username,
                'phone': user.phone,
                'address': user.address,
            }
            session['user_id'] = user.id
            session['user_name'] = user.username
            session['user_phone'] = user.phone
            session['user_address'] = user.address
        else:
            result['error'] = 1
    return result


@app.route('/logout')
def logout():
    """
    Logging user out
    :return:
    {
        error: 0,
    }
    """
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_phone', None)
    session.pop('user_address', None)
    return {
        'error': 0
    }


@app.route('/menu')
def menu():
    filters = request.args
    # filtering out all not valid keys
    filters = {k: v for (k, v) in filters.items() if k in {'type', 'base', 'crust'}}

    products = Product.get_by_filters(filters)
    products = [v.to_dict() for v in products]

    return {
        'error': 0,
        'products': products
    }


@app.route('/make_order', methods=['POST'])
def make_order():
    result = {
        'error': 1,
        'order': None
    }

    if request.get_json() is None or\
            request.get_json().get('order') is None\
            or request.get_json().get('name') is None\
            or request.get_json().get('phone') is None\
            or request.get_json().get('address') is None:
        return result

    if 'user_id' in session and session['user_name'] == request.get_json().get('name'):
        pass
    else:
        # Registering a new user using provided name and address
        user = User.load_user_by_phone(request.get_json().get('phone'))
        if user is None:
            user = User(username=request.get_json().get('name'), address=request.get_json().get('address'), phone=request.get_json().get('phone'))
            db.session.add(user)
            db.session.commit()

        session['user_id'] = user.id
        session['user_name'] = user.username
        session['user_phone'] = user.phone
        session['user_address'] = user.address

    user_result = {
        'id': session['user_id'],
        'name': session['user_name'],
        'phone': session['user_phone'],
        'address': session['user_address']
    }
    result['user'] = user_result

    o = Order(user_id=user_result['id'],
              username=request.get_json().get('name'),
              address=request.get_json().get('address'),
              phone=request.get_json().get('phone'))

    o.total_price = SERVICE_INFO['delivery_price']

    order_products = request.get_json().get('order')
    for order_product in order_products:
        p = Product.query.get(order_product['id'])
        if p is None or order_product['quantity'] is None:
            result.error = 2
            return result

        o.total_price += order_product['quantity'] * p.price

        po = ProductOrder(product=p, quantity=order_product['quantity'], order=o)
        db.session.add(po)

    o.status = OrderStatus.ORDERED
    db.session.add(o)
    db.session.commit()

    result['error'] = 0
    result['order'] = o.to_dict()
    return result


@app.route('/my_orders')
def my_orders():
    result = {
        'error': 1,
        'orders_list': None
    }
    if 'user_id' not in session:
        return result

    result['error'] = 0
    orders_list = Order.get_my_orders(session['user_id'])
    for order in orders_list:
        now = datetime.utcnow().timestamp()
        create_timestamp = order.create_timestamp.timestamp()
        time_passed = now - create_timestamp
        if time_passed > ORDER_STATUS_EXPIRATION['DELIVERED_AFTER']:
            order.status = OrderStatus.DELIVERED
            status_countdown = 0
        elif time_passed > ORDER_STATUS_EXPIRATION['READY_AFTER']:
            order.status = OrderStatus.READY
            status_countdown = ORDER_STATUS_EXPIRATION['DELIVERED_AFTER'] - time_passed
        elif time_passed > ORDER_STATUS_EXPIRATION['CONFIRMED_AFTER']:
            order.status = OrderStatus.CONFIRMED
            status_countdown = ORDER_STATUS_EXPIRATION['READY_AFTER'] - time_passed
        else:
            status_countdown = ORDER_STATUS_EXPIRATION['CONFIRMED_AFTER'] - time_passed

        order.status_countdown = status_countdown

        db.session.commit()

    result['orders_list'] = [order.to_dict() for order in orders_list]

    return result


@app.route('/service_info')
def service_info():
    return {
        'info': SERVICE_INFO,
        'error': 0
    }

