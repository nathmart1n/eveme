"""
EVEME index (logout) view.

URLs include:
/logout/
"""
from flask import redirect, url_for
from flask_login import login_required, logout_user
import eveme


@eveme.app.route("/logout")
@login_required
def logout():
    """Execute logout if logged in."""
    logout_user()
    return redirect(url_for("show_index"))
