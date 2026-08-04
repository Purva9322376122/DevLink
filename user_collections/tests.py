import pytest
from django.urls import reverse


@pytest.fixture
def collection(db, user):
    from user_collections.models import Collection
    return Collection.objects.create(owner=user, name='Test Collection')


@pytest.mark.django_db
class TestCollectionServices:
    def test_create_collection(self, user):
        from user_collections.services import create_collection
        col = create_collection(user, 'My Col', 'desc')
        assert col.owner == user
        assert col.name == 'My Col'

    def test_update_collection(self, user, collection):
        from user_collections.services import update_collection
        update_collection(collection, user, {'name': 'New Name'})
        collection.refresh_from_db()
        assert collection.name == 'New Name'

    def test_delete_collection(self, user, collection):
        from user_collections.models import Collection
        from user_collections.services import delete_collection
        pk = collection.pk
        delete_collection(collection, user)
        assert not Collection.objects.filter(pk=pk).exists()

    def test_add_item_to_collection(self, user, collection):
        from user_collections.models import CollectionItem
        from user_collections.services import add_item
        add_item(collection, user, 'problem', 1)
        assert CollectionItem.objects.filter(collection=collection, object_id=1).exists()

    def test_remove_item_from_collection(self, user, collection):
        from user_collections.models import CollectionItem
        from user_collections.services import add_item, remove_item
        item = add_item(collection, user, 'problem', 1)
        remove_item(collection, user, item.id)
        assert not CollectionItem.objects.filter(id=item.id).exists()

    def test_permission_error_on_edit_by_non_owner(self, user, collection, user_factory):
        from user_collections.services import update_collection
        other = user_factory(username='cother', email='co@x.com')
        with pytest.raises(PermissionError):
            update_collection(collection, other, {'name': 'X'})


@pytest.mark.django_db
class TestCollectionViews:
    def test_collection_list_requires_login(self, client):
        url = reverse('collections:list')
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_collection_list_returns_200(self, auth_client):
        url = reverse('collections:list')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_collection_detail_public_accessible(self, client, collection):
        url = reverse('collections:detail', kwargs={'pk': collection.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_create_collection_view(self, auth_client, user):
        from user_collections.models import Collection
        url = reverse('collections:create')
        response = auth_client.post(url, {'name': 'New Col', 'description': 'desc', 'is_public': 'on'})
        assert response.status_code in (200, 302)
        assert Collection.objects.filter(owner=user, name='New Col').exists()
