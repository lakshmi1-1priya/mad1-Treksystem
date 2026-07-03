from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """blockks access unless a user is logged in any role"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return f(*args,**kwargs)
    return wrapper

def roles_required(*allowed_roles):
    """
    only for reg users
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args,**kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("main.login"))
            if session.get("role") not in allowed_roles:
                flash("You ddo not have permission to acces that page.", "danger")
                return redirect(url_for("main.dashboard_redirect"))
            return f(*args,**kwargs)
        return wrapper
    return decorator


 