from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'error')
                return redirect(url_for('login'))
            if session.get('role') != role:
                flash(f'Only {role}s can do that.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated
    return wrapper