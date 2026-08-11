from django.urls import path, re_path
from . import api

urlpatterns = [path("", api.cart_detail), path("checkout/", api.checkout), path("orders/", api.orders), path("discount/", api.discount), path("items/", api.add_item), path("items/<int:item_id>/", api.cart_item), re_path(r"^export\.csv/?$", api.cart_export_csv)]
