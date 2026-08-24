from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_alter_reservation_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventory",
            name="on_hand_quantity",
            field=models.DecimalField(decimal_places=6, default=0, max_digits=18, validators=[MinValueValidator(Decimal("0"))]),
        ),
        migrations.AlterField(
            model_name="inventory",
            name="reserved_quantity",
            field=models.DecimalField(decimal_places=6, default=0, max_digits=18, validators=[MinValueValidator(Decimal("0"))]),
        ),
    ]
