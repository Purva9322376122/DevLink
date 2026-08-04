from django.contrib.auth.models import User
from .models import Collection, CollectionItem


def create_collection(owner: User, name: str, description: str = '', is_public: bool = True) -> Collection:
    return Collection.objects.create(owner=owner, name=name, description=description, is_public=is_public)


def update_collection(collection: Collection, user: User, data: dict) -> Collection:
    if collection.owner != user:
        raise PermissionError("Only the collection owner can edit it.")
    for field in ('name', 'description', 'is_public'):
        if field in data:
            setattr(collection, field, data[field])
    collection.slug = ''  # regenerate
    collection.save()
    return collection


def delete_collection(collection: Collection, user: User) -> None:
    if collection.owner != user:
        raise PermissionError("Only the collection owner can delete it.")
    collection.delete()


def add_item(collection: Collection, user: User, item_type: str, object_id: int, note: str = '') -> CollectionItem:
    if collection.owner != user:
        raise PermissionError("Only the collection owner can add items.")
    item, _ = CollectionItem.objects.get_or_create(
        collection=collection, item_type=item_type, object_id=object_id,
        defaults={'note': note}
    )
    return item


def remove_item(collection: Collection, user: User, item_id: int) -> None:
    if collection.owner != user:
        raise PermissionError("Only the collection owner can remove items.")
    CollectionItem.objects.filter(collection=collection, id=item_id).delete()
