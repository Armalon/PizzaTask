
def clear_session(session):
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_phone', None)
    session.pop('user_address', None)


def session_to_user_result(session):
    return {
        'id': session['user_id'],
        'name': session['user_name'],
        'phone': session['user_phone'],
        'address': session['user_address'],
    }


def user_to_session(session, user):
    session['user_id'] = user.id
    session['user_name'] = user.username
    session['user_phone'] = user.phone
    session['user_address'] = user.address