from django.urls import path

from ecommerce.views import HomeView, ItemDetailView, CheckoutView, add_to_cart, OrderSummaryView, \
    remove_from_cart, remove_single_item_from_cart, AddCouponView, OrdersView, OrderDetailsView

app_name = "ecommerce"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    # path('search/', SearchResultsView.as_view(), name='search-results'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrdersView.as_view(), name='orders'),
    path('order-details/<pk>/', OrderDetailsView.as_view(), name='order-details'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
]
