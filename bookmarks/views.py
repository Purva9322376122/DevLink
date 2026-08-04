from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .selectors import (
    get_bookmarked_problems,
    get_bookmarked_solutions,
    get_bookmarked_opportunities,
)


@login_required
def bookmark_list(request):
    return render(request, 'bookmarks/bookmark_list.html', {
        'problems': get_bookmarked_problems(request.user),
        'solutions': get_bookmarked_solutions(request.user),
        'opportunities': get_bookmarked_opportunities(request.user),
    })


@login_required
@require_POST
def toggle_bookmark_view(request, content_type_id: int, object_id: int):
    from .services import toggle_bookmark
    from django.contrib.contenttypes.models import ContentType
    try:
        ct = ContentType.objects.get(id=content_type_id)
        obj = ct.get_object_for_this_type(pk=object_id)
        bookmarked, total = toggle_bookmark(request.user, obj)
        return JsonResponse({'bookmarked': bookmarked, 'total': total})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
