from django.contrib import admin

from ecommerce.models import Item, OrderItem, Order, Payment, Coupon, Address, UserProfile


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'being_delivered',
                    'received',
                    'shipping_address',
                    'billing_address',
                    'payment',
                    'coupon',
                    'added_at',
                    'updated_at',
                    ]
    list_display_links = [
        'user',
        'shipping_address',
        'billing_address',
        'payment',
        'coupon'
    ]
    list_filter = ['ordered',
                   'being_delivered',
                   'received']
    search_fields = [
        'user__username',
        'ref_code'
    ]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'discount_price', 'category', 'label', 'slug']
    list_filter = ['category', 'label']
    search_fields = ['title']


class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'expire', 'amount']


admin.site.register(Item, ItemAdmin)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserProfile)
