
def clear_session(session):
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_phone', None)
    session.pop('user_address', None)