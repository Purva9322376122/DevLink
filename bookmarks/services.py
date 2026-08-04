from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType


def toggle_bookmark(user: User, obj) -> tuple:
    """Toggle bookmark. Returns (is_bookmarked, total_count)."""
    from .models import Bookmark
    ct = ContentType.objects.get_for_model(obj)
    bookmark, created = Bookmark.objects.get_or_create(
        user=user, content_type=ct, object_id=obj.pk
    )
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True
    total = Bookmark.objects.filter(content_type=ct, object_id=obj.pk).count()
    return bookmarked, total


def is_bookmarked(user: User, obj) -> bool:
    if not user.is_authenticated:
        return False
    from .models import Bookmark
    ct = ContentType.objects.get_for_model(obj)
    return Bookmark.objects.filter(user=user, content_type=ct, object_id=obj.pk).exists()


def get_user_bookmarks(user: User):
    from .models import Bookmark
    return Bookmark.objects.filter(user=user).select_related('content_type')
