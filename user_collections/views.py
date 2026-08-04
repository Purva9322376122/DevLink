from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Collection, CollectionItem
from .selectors import get_public_collections, get_user_collections
from .services import add_item, create_collection, delete_collection, remove_item, update_collection


@login_required
def collection_list(request):
    my_collections = get_user_collections(request.user)
    public = get_public_collections(query=request.GET.get('q', ''))
    return render(request, 'collections/collection_list.html', {
        'my_collections': my_collections,
        'public_collections': public,
        'query': request.GET.get('q', ''),
    })


def collection_detail(request, pk):
    collection = get_object_or_404(Collection, pk=pk)
    if not collection.is_public and collection.owner != request.user:
        from django.http import Http404
        raise Http404
    items = collection.items.all()
    resolved_items = []
    for item in items:
        obj = item.get_item()
        if obj:
            resolved_items.append({'item': item, 'obj': obj})
    return render(request, 'collections/collection_detail.html', {
        'collection': collection,
        'resolved_items': resolved_items,
    })


@login_required
def create_collection_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '')
        is_public = request.POST.get('is_public') == 'on'
        if not name:
            from django.contrib import messages
            messages.error(request, 'Collection name is required.')
            return redirect('collections:list')
        col = create_collection(request.user, name, description, is_public)
        return redirect('collections:detail', pk=col.pk)
    return render(request, 'collections/collection_form.html', {'action': 'Create'})


@login_required
def edit_collection_view(request, pk):
    collection = get_object_or_404(Collection, pk=pk, owner=request.user)
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name', '').strip(),
            'description': request.POST.get('description', ''),
            'is_public': request.POST.get('is_public') == 'on',
        }
        try:
            update_collection(collection, request.user, data)
            return redirect('collections:detail', pk=collection.pk)
        except PermissionError as e:
            from django.contrib import messages
            messages.error(request, str(e))
    return render(request, 'collections/collection_form.html', {
        'collection': collection, 'action': 'Edit',
    })


@login_required
@require_POST
def delete_collection_view(request, pk):
    collection = get_object_or_404(Collection, pk=pk, owner=request.user)
    try:
        delete_collection(collection, request.user)
    except PermissionError:
        pass
    return redirect('collections:list')


@login_required
@require_POST
def add_item_view(request):
    collection_id = request.POST.get('collection_id')
    item_type = request.POST.get('item_type')
    object_id = request.POST.get('object_id')
    note = request.POST.get('note', '')
    try:
        collection = Collection.objects.get(pk=collection_id, owner=request.user)
        add_item(collection, request.user, item_type, int(object_id), note)
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def remove_item_view(request, item_id):
    item = get_object_or_404(CollectionItem, pk=item_id, collection__owner=request.user)
    collection_pk = item.collection_id
    remove_item(item.collection, request.user, item_id)
    return redirect('collections:detail', pk=collection_pk)
