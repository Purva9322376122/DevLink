"""
Solutions services — all business logic and mutation functions.
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.utils import timezone

from .models import Comment, Solution, SolutionRevision, Vote


def toggle_solution_vote(user: User, solution: Solution) -> tuple[bool, int]:
    """
    Toggle an upvote for *user* on *solution*.
    Returns (voted, total_votes).
    """
    existing = Vote.objects.filter(user=user, solution=solution)
    if existing.exists():
        existing.delete()
        voted = False
    else:
        Vote.objects.create(user=user, solution=solution)
        voted = True
    return voted, solution.votes.count()


def create_solution_revision(solution: Solution, editor: User) -> SolutionRevision:
    """Snapshot current solution state before an edit."""
    last = SolutionRevision.objects.filter(solution=solution).order_by('-version').first()
    version = (last.version + 1) if last else 1
    return SolutionRevision.objects.create(
        solution=solution,
        editor=editor,
        explanation=solution.explanation,
        code=solution.code or '',
        language=solution.language,
        version=version,
    )


def update_solution(solution: Solution, user: User, data: dict) -> Solution:
    """Update a solution and save a revision. Only the owner may edit."""
    if solution.user != user:
        raise PermissionError("Only the solution owner can edit it.")
    create_solution_revision(solution, user)
    for field in ('explanation', 'code', 'language'):
        if field in data:
            setattr(solution, field, data[field])
    solution.save()
    return solution


def soft_delete_solution(solution: Solution, user: User) -> None:
    """Soft-delete a solution. Only the owner, problem author, or staff may delete it."""
    if solution.user != user and not user.is_staff and not user.is_superuser and solution.problem.user != user:
        raise PermissionError("Only the solution owner, problem author, or staff can delete it.")
    solution.is_deleted = True
    solution.save(update_fields=['is_deleted'])


def edit_comment(comment: Comment, user: User, new_text: str) -> Comment:
    """Edit a comment. Only the owner may edit."""
    if comment.user != user:
        raise PermissionError("Only the comment owner can edit it.")
    comment.text = new_text
    comment.is_edited = True
    comment.edited_at = timezone.now()
    comment.save()
    return comment


def delete_comment(comment: Comment, user: User) -> None:
    """Soft-delete a comment. Only the owner may delete."""
    if comment.user != user:
        raise PermissionError("Only the comment owner can delete it.")
    comment.is_deleted = True
    comment.save(update_fields=['is_deleted'])


def render_markdown(text: str) -> str:
    """
    Render Markdown to safe HTML.
    Supports fenced code blocks, tables, task lists.
    Output is sanitized with bleach and safe link parsing.
    """
    import markdown
    import bleach
    import re

    if not text:
        return ''

    # Clean unparsed Django template tags in raw markdown text to prevent broken links
    text = re.sub(r'\{%\s*url\s+[\'"]accounts:profile[\'"]\s+([^\s%}]+)\s*%\}', r'/accounts/profile/\1/', text)
    text = re.sub(r'\{%.*?%\}', '', text)
    text = re.sub(r'\{\{.*?\}\}', '', text)

    ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
        'p', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'hr', 'br',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'img', 'del', 'input',
    ]
    ALLOWED_ATTRS = {
        **bleach.sanitizer.ALLOWED_ATTRIBUTES,
        'code': ['class'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'a': ['href', 'title', 'rel'],
        'input': ['type', 'checked', 'disabled'],
        'th': ['align'],
        'td': ['align'],
    }

    html = markdown.markdown(
        text,
        extensions=[
            'fenced_code', 'tables', 'nl2br', 'sane_lists',
            'toc', 'codehilite',
        ],
        extension_configs={
            'codehilite': {'css_class': 'highlight', 'guess_lang': False},
        },
    )

    cleaned_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    # Sanitize any href containing literal {% or %7B or unescaped template tags
    cleaned_html = re.sub(r'href="[^"]*(?:%7B|\{%|%7D|\%\})[^"]*"', 'href="#"', cleaned_html)
    return cleaned_html
