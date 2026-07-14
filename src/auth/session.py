import streamlit as st

from src.database import get_db_session
from src.models import User


SESSION_USER_ID_KEY = "user_id"


def set_current_user(user_id):
    st.session_state[SESSION_USER_ID_KEY] = int(user_id)


def get_current_user_id():
    return st.session_state.get(SESSION_USER_ID_KEY)


def get_current_user():
    user_id = get_current_user_id()
    if user_id is None:
        return None

    with get_db_session() as session:
        user = session.get(User, user_id)

    if user is None:
        clear_current_user()
    return user


def clear_current_user():
    st.session_state.pop(SESSION_USER_ID_KEY, None)
