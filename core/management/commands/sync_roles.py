"""ساخت/به‌روزرسانی گروه‌های نقش و دسترسی‌ها."""
from django.core.management.base import BaseCommand

from accounts.roles import ROLE_MATRIX, sync_role_groups


class Command(BaseCommand):
    help = "گروه‌های نقش (مدیر سیستم، مدیر فروش، کارشناس فروش، انباردار، مالی، محتوا، پشتیبانی) را می‌سازد."

    def handle(self, *args, **options):
        groups = sync_role_groups()
        for role, group in groups.items():
            perms = group.permissions.count()
            self.stdout.write(self.style.SUCCESS(
                f"{ROLE_MATRIX[role]['group']}: {perms} دسترسی"
            ))
        self.stdout.write(self.style.SUCCESS(f"{len(groups)} گروه نقش همگام شد."))
