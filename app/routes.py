from app import app, session, request, db
from datetime import datetime
import sqlite3

from app.models import User, Product, ProductOrder, Order, OrderStatus

import app.helpers as helpers

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
        # Taking user info from a current session
        result['user'] = helpers.session_to_user_result(session)
    else:
        user = None

        # If user_id is provided (was stored on a frontend part)
        if request.get_json() is not None \
                and request.get_json().get('user_id') is not None:
            user = User.load_user(int(request.get_json().get('user_id')))

        # Getting a random user if user_id is not provided or not found in DB
        if user is None:
            try:
                user = User.load_random_user()
            except Exception as ex:
                result['error'] = 2
                # or raise further maybe
                return result

        # Setting data to the session and returning a result
        if user is not None:
            helpers.user_to_session(session, user)
            result['user'] = helpers.session_to_user_result(session)
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

    # Clearing all user data from session
    helpers.clear_session(session)

    return {
        'error': 0
    }


@app.route('/menu')
def menu():
    """
    Getting all the menu elements
    req.args: {
        filters: {
            'type': 'String',
            'base': 'String',
            'crust': 'String',
        }
    }
    :return:
    {
        error: 0,
        products: [Product]
    }
    """

    # note: Filters are not provided from a Frontend at the moment,
    # all the filtration is implemented on a Frontend part
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
    """
    Creating an order
    req.args: {
        order: [
            {
                'id': 123,
                'quantity': 2
            },
        ],
        name: 'String',
        phone: 'String',
        address: 'String'
    }
    :return:
    {
        error: 0,
        order: Order
    }
    """

    result = {
        'error': 1,
        'order': None
    }

    # Check if all the reuired params are passed
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

        # Setting user data to the session
        helpers.user_to_session(session, user)

    user_result = helpers.session_to_user_result(session)
    result['user'] = user_result

    # Creating an order
    o = Order(user_id=user_result['id'],
              username=request.get_json().get('name'),
              address=request.get_json().get('address'),
              phone=request.get_json().get('phone'))

    o.total_price = SERVICE_INFO['delivery_price']

    # Setting OrderProducts to the order
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
    """
    Getting all user orders using session data
    req.args: {
    }
    :return:
    {
        error: 0,
        orders_list: [Order]
    }
    """

    result = {
        'error': 1,
        'orders_list': None
    }
    if 'user_id' not in session:
        return result

    result['error'] = 0

    # Getting my orders list
    orders_list = Order.get_my_orders(session['user_id'])
    for order in orders_list:
        # Calculating an order status
        # and setting it back to the order
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

        # setting an status_countdown and returning it back to the Frontend
        order.status_countdown = status_countdown

        db.session.commit()

    result['orders_list'] = [order.to_dict() for order in orders_list]

    return result


@app.route('/service_info')
def service_info():
    """
    Returning service info
    req.args: {
    }
    :return:
    {
        error: 0,
        info: {
            'delivery_price': 4,
            'usd_to_eur_multiplier': 1.16,
        }
    }
    """
    return {
        'info': SERVICE_INFO,
        'error': 0
    }

