"""Views, one for each EVEME page."""
from eveme.views.index import show_index
from eveme.views.contact import show_contact
from eveme.views.about import show_about
from eveme.views.auth.login import login, character, callback
from eveme.views.auth.logout import logout
from eveme.views.settings import show_settings