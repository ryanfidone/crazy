from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_library_member_group(sender, **kwargs):
    if sender.name != "catalog":
        return
    group, _ = Group.objects.get_or_create(name="LibraryMember")
    codenames = [
        "view_book", "view_author", "view_genre", "view_bookinstance",
    ]
    permissions = Permission.objects.filter(
        content_type__app_label="catalog",
        codename__in=codenames,
    )
    group.permissions.set(permissions)
