"""
Problems services — business logic for problems module.
"""
from __future__ import annotations
from django.contrib.auth.models import User
from django.utils.text import slugify


def record_problem_view(problem, request) -> None:
    """Record a view for a problem (unique per user/IP per day)."""
    from .models import ProblemView
    from django.db.models import F
    from django.utils import timezone

    user = request.user if request.user.is_authenticated else None
    ip = _get_ip(request)
    today = timezone.now().date()

    # Check for duplicate view today
    qs = ProblemView.objects.filter(problem=problem, viewed_at__date=today)
    if user:
        if qs.filter(user=user).exists():
            return
    elif ip:
        if qs.filter(ip_address=ip, user=None).exists():
            return

    ProblemView.objects.create(problem=problem, user=user, ip_address=ip)
    # Atomic increment
    from .models import Problem
    Problem.objects.filter(pk=problem.pk).update(view_count=F('view_count') + 1)


def create_problem_revision(problem, editor: User) -> None:
    """Snapshot the current state of a problem before an edit."""
    from .models import ProblemRevision
    last = ProblemRevision.objects.filter(problem=problem).order_by('-version').first()
    version = (last.version + 1) if last else 1
    ProblemRevision.objects.create(
        problem=problem,
        editor=editor,
        title=problem.title,
        description=problem.description,
        difficulty=problem.difficulty,
        version=version,
    )


def update_problem(problem, user: User, data: dict) -> None:
    """Update a problem and create a revision."""
    create_problem_revision(problem, user)
    for field in ('title', 'description', 'difficulty', 'language', 'category'):
        if field in data:
            setattr(problem, field, data[field])
    problem.save()


def soft_delete_problem(problem, user: User) -> None:
    """Soft-delete a problem."""
    if problem.user != user and not user.is_staff and not user.is_superuser:
        raise PermissionError("You can only delete your own problems.")
    problem.is_deleted = True
    problem.save(update_fields=['is_deleted'])


def submit_report(reporter: User, content_type: str, object_id: int, reason: str, description: str = '') -> None:
    """Submit a content report."""
    from .models import Report
    Report.objects.get_or_create(
        reporter=reporter,
        content_type=content_type,
        object_id=object_id,
        defaults={'reason': reason, 'description': description},
    )


def get_or_create_tag(name: str) -> tuple:
    from .models import Tag
    slug = slugify(name)
    tag, created = Tag.objects.get_or_create(
        name=name.lower().strip(),
        defaults={'slug': slug or name.lower().strip()}
    )
    return tag, created


def _get_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
