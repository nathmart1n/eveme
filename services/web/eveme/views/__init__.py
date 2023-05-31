"""Views, one for each EVEME page."""
from eveme.views.index import show_index
from eveme.views.contact import show_contact
from eveme.views.about import show_about
from eveme.views.auth.login import login, callback
from eveme.views.auth.logout import logout
from eveme.views.settings import show_settings, structure_mod
from eveme.views.orders import show_orders
from eveme.views.character import character
from eveme.views.imports import show_imports
from eveme.views.station_trading import show_station_trading
