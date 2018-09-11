from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r"^home$", home, name="home"),
    url(r"^cart$", cart, name="cart"),
    url(r"^market$", market, name="market"),
    url(r"^market_with_params/(\d+)/(\d+)/(\d+)", market_with_params, name="market_with_params"),
    url(r"^mine$", mine, name="mine"),
    url(r"^register$", RegisterAPI.as_view(), name="register"),
    url(r"^login$", LoginAPI.as_view(), name="login"),
    url(r"^confirm/(.*)", confirm),
    url(r"^logout$", logout_api, name="logout"),
    url(r"^cartapi$", cart_api, name="cart_api"),
    url(r"^cart-status$", cart_status_api),
    url(r"^select_all_api$", select_all_api),
    url(r"^cartitem_api$", cartitem_api),
    url(r"^order$", order_api, name="order")
]