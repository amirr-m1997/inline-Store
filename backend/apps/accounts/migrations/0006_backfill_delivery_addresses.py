from django.db import migrations


def backfill_addresses(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    CustomerAddress = apps.get_model("accounts", "CustomerAddress")
    Cart = apps.get_model("carts", "Cart")
    for user in User.objects.all():
        if CustomerAddress.objects.filter(user=user).exists():
            continue
        cart = Cart.objects.filter(user=user, status="checked_out").exclude(shipping_address="").order_by("-updated_at").first()
        if not cart:
            continue
        CustomerAddress.objects.create(
            user=user, title="نشانی پیش‌فرض",
            recipient_name=f"{cart.customer_first_name} {cart.customer_last_name}".strip(),
            recipient_phone=cart.customer_phone, province=cart.shipping_province,
            city=cart.shipping_city, postal_code=cart.shipping_postal_code,
            address=cart.shipping_address, is_default=True,
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_customer_profile_and_addresses"), ("carts", "0003_cart_customer_fields")]
    operations = [migrations.RunPython(backfill_addresses, migrations.RunPython.noop)]
