import random
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.views.generic.base import View

from ecommerce.forms import CheckoutForm, CouponForm
from ecommerce.models import Item, OrderItem, Order, Address, Coupon, Payment


def item_list(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, 'home.html', context)


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"

    def get_queryset(self):
        query = self.request.GET.get('query')
        filter_val = self.request.GET.get('filter')
        order = self.request.GET.get('orderby', 'title')
        if filter_val:
            object_list = Item.objects.filter(category=filter_val).order_by(order)
        elif query:
            object_list = Item.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
        else:
            object_list = Item.objects.filter().order_by(order)
        return object_list

    # def get_queryset(self):
    #     query = self.request.GET.get('query')
    #     filter_val = self.request.GET.get('filter')
    #     order = self.request.GET.get('orderby', 'title')
    #     if filter_val:
    #         new_context = Item.objects.filter(category=filter_val).order_by(order)
    #     elif query:
    #         new_context = Item.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    #     else:
    #         new_context = Item.objects.filter().order_by(order)
    #     return new_context
    #
    # def get_context_data(self, **kwargs):
    #     context = super(HomeView, self).get_context_data(**kwargs)
    #     context['query'] = self.request.GET.get('query')
    #     context['filter'] = self.request.GET.get('filter')
    #     context['orderby'] = self.request.GET.get('orderby', 'title')
    #     return context


# class SearchResultsView(ListView):
#     model = Item
#     paginate_by = 10
#     template_name = 'search-results.html'
#
#     def get_queryset(self):
#         query = self.request.GET.get('q')
#         object_list = Item.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
#         return object_list


class OrdersView(LoginRequiredMixin, ListView):
    model = Order
    paginate_by = 10
    template_name = "orders.html"

    def get_queryset(self):
        if self.request.user.is_superuser:
            object_list = Order.objects.all().order_by('-ordered_date')
        else:
            object_list = Order.objects.filter(user=self.request.user.pk).order_by('-ordered_date')
        return object_list


class OrderDetailsView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "order-details.html"


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("ecommerce:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("ecommerce:product", slug=slug)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("ecommerce:product", slug=slug)


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("ecommerce:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("ecommerce:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("ecommerce:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("ecommerce:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("ecommerce:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("ecommerce:product", slug=slug)


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})

            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("ecommerce:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.warning(self.request, "No default shipping address available")
                        return redirect('ecommerce:checkout')
                else:
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    shipping_contact = form.cleaned_data.get('shipping_contact')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            contact=shipping_contact,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.warning(self.request, "Please fill in the required shipping address fields")
                        return redirect("ecommerce:checkout")

                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get('same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.warning(self.request, "No default billing address available")
                        return redirect('ecommerce:checkout')
                else:
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')
                    billing_contact = form.cleaned_data.get('billing_contact')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            contact=billing_contact,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.warning(self.request, "Please fill in the required billing address fields")
                        return redirect("ecommerce:checkout")

                payment = Payment()
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("ecommerce:checkout")


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        if not coupon.expire:
            return coupon
        else:
            messages.warning(request, "This coupon expired!")
            return None
    except ObjectDoesNotExist:
        messages.warning(request, "This coupon does not exist")
        # return redirect("ecommerce:checkout")
        return None


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                coupon = get_coupon(self.request, code)
                if not coupon:
                    return redirect("ecommerce:checkout")
                order.coupon = coupon
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("ecommerce:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("ecommerce:checkout")
