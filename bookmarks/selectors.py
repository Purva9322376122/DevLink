from django.contrib.auth.models import User


def get_bookmarked_problems(user: User):
    from .models import Bookmark
    from django.contrib.contenttypes.models import ContentType
    from problems.models import Problem
    ct = ContentType.objects.get_for_model(Problem)
    ids = Bookmark.objects.filter(user=user, content_type=ct).values_list('object_id', flat=True)
    return Problem.objects.filter(id__in=ids)


def get_bookmarked_solutions(user: User):
    from .models import Bookmark
    from django.contrib.contenttypes.models import ContentType
    from solutions.models import Solution
    ct = ContentType.objects.get_for_model(Solution)
    ids = Bookmark.objects.filter(user=user, content_type=ct).values_list('object_id', flat=True)
    return Solution.objects.filter(id__in=ids).select_related('problem')


def get_bookmarked_opportunities(user: User):
    from .models import Bookmark
    from django.contrib.contenttypes.models import ContentType
    from opportunities.models import Opportunity
    ct = ContentType.objects.get_for_model(Opportunity)
    ids = Bookmark.objects.filter(user=user, content_type=ct).values_list('object_id', flat=True)
    return Opportunity.objects.filter(id__in=ids)
