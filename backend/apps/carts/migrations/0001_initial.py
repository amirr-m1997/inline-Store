import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("catalog", "0001_initial")]
    operations = [
        migrations.CreateModel(name="Cart", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("guest_token", models.UUIDField(blank=True, default=uuid.uuid4, null=True, unique=True)), ("status", models.CharField(choices=[("active", "Active"), ("checked_out", "Checked out"), ("abandoned", "Abandoned")], default="active", max_length=16)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="carts", to=settings.AUTH_USER_MODEL))]),
        migrations.CreateModel(name="CartItem", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("cart", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="carts.cart")), ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cart_items", to="catalog.product"))]),
        migrations.AddConstraint(model_name="cartitem", constraint=models.UniqueConstraint(fields=("cart", "product"), name="cart_product_unique")),
    ]
