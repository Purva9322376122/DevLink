from django.contrib.auth.models import User
from django.db.models import QuerySet, Q


def get_user_collections(user: User) -> QuerySet:
    from .models import Collection
    return Collection.objects.filter(owner=user).prefetch_related('items')


def get_public_collections(query: str = '') -> QuerySet:
    from .models import Collection
    qs = Collection.objects.filter(is_public=True).select_related('owner')
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return qs


def get_collection_or_none(pk: int, user: User):
    from .models import Collection
    try:
        col = Collection.objects.get(pk=pk)
        if col.is_public or col.owner == user:
            return col
        return None
    except Collection.DoesNotExist:
        return None
