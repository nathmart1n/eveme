"""
EVEME logout view.

URLs include:
/logout/
"""
from flask import redirect, url_for
from flask_login import login_required, logout_user
import eveme
import time


@eveme.app.route("/logout")
@login_required
def logout():
    """Execute logout if logged in."""
    start_time = time.time()
    logout_user()
    eveme.app.logger.info("--- logout() took %s seconds ---" % (time.time() - start_time))
    return redirect(url_for("show_index"))
