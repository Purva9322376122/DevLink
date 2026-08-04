from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Problem, ProblemRevision, Report, Tag
from .selectors import (
    get_popular_problems,
    get_popular_tags,
    get_problem_revision_history,
    get_problems,
    get_related_problems,
    get_tag_suggestions,
    get_trending_problems,
    get_unresolved_reports,
)
from .services import (
    create_problem_revision,
    get_or_create_tag,
    record_problem_view,
    soft_delete_problem,
    submit_report,
    update_problem,
)


# ── Existing views (unchanged) ────────────────────────────────────────────


def problem_list(request):
    query = request.GET.get('q')
    tag = request.GET.get('tag')
    difficulty = request.GET.get('difficulty')
    language = request.GET.get('language')
    sort = request.GET.get('sort', 'newest')

    ordering_map = {
        'newest': '-created_at',
        'popular': '-view_count',
        'trending': '-created_at',
    }
    ordering = ordering_map.get(sort, '-created_at')

    if sort == 'trending':
        problems = get_trending_problems(limit=50)
    else:
        problems = get_problems(
            query=query, tag=tag, difficulty=difficulty,
            language=language, ordering=ordering,
        )

    popular_tags = get_popular_tags(limit=20)
    return render(request, 'problem_list.html', {
        'problems': problems,
        'query': query,
        'selected_tag': tag,
        'selected_difficulty': difficulty,
        'selected_language': language,
        'selected_sort': sort,
        'popular_tags': popular_tags,
    })


def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id, is_deleted=False)
    record_problem_view(problem, request)
    related = get_related_problems(problem)
    from solutions.services import render_markdown
    return render(request, 'problem_detail.html', {
        'problem': problem,
        'related_problems': related,
        'rendered_description': render_markdown(problem.description),
    })


@login_required
def create_problem(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        difficulty = request.POST.get('difficulty', '')
        language = request.POST.get('language', '')
        category = request.POST.get('category', '')
        tags_input = request.POST.get('tags', '')

        if not title:
            messages.error(request, "Title is required.")
            return redirect('create_problem')
        if not difficulty:
            messages.error(request, "Please select a difficulty level.")
            return redirect('create_problem')

        problem = Problem.objects.create(
            user=request.user,
            title=title,
            description=description,
            difficulty=difficulty,
            language=language,
            category=category,
        )

        if tags_input:
            tag_names = list(set(t.strip().lower() for t in tags_input.split(',') if t.strip()))
            if len(tag_names) > 5:
                messages.error(request, "You can only add up to 5 tags.")
                problem.delete()
                return redirect('create_problem')
            for name in tag_names:
                tag, _ = get_or_create_tag(name)
                problem.tags.add(tag)
                Tag.objects.filter(pk=tag.pk).update(usage_count=tag.usage_count + 1)

        # Award reputation for posting a problem
        try:
            from reputation.services import award_reputation
            award_reputation(request.user, 'problem_posted', f'Posted problem: {title}')
        except Exception:
            pass

        messages.success(request, "Problem created successfully.")
        return redirect('problem_detail', problem_id=problem.id)

    return render(request, 'problem_create.html', {'languages': _LANGUAGE_CHOICES})


# ── New views ─────────────────────────────────────────────────────────────


@login_required
def edit_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id, is_deleted=False)
    if problem.user != request.user and not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You can only edit your own problems.")
        return redirect('problem_detail', problem_id=problem.id)

    if request.method == 'POST':
        data = {
            'title': request.POST.get('title', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'difficulty': request.POST.get('difficulty', problem.difficulty),
            'language': request.POST.get('language', ''),
            'category': request.POST.get('category', ''),
        }
        if not data['title']:
            messages.error(request, "Title cannot be empty.")
            return redirect('edit_problem', problem_id=problem.id)
        update_problem(problem, request.user, data)

        # Update tags
        tags_input = request.POST.get('tags', '')
        problem.tags.clear()
        if tags_input:
            for name in set(t.strip().lower() for t in tags_input.split(',') if t.strip()):
                tag, _ = get_or_create_tag(name)
                problem.tags.add(tag)

        messages.success(request, "Problem updated.")
        return redirect('problem_detail', problem_id=problem.id)

    current_tags = ', '.join(t.name for t in problem.tags.all())
    return render(request, 'problems/problem_edit.html', {
        'problem': problem,
        'current_tags': current_tags,
        'languages': _LANGUAGE_CHOICES,
    })


@login_required
@require_POST
def delete_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id, is_deleted=False)
    try:
        soft_delete_problem(problem, request.user)
        messages.success(request, "Problem deleted.")
    except PermissionError as e:
        messages.error(request, str(e))
    return redirect('problem_list')


def problem_history(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    revisions = get_problem_revision_history(problem)
    return render(request, 'problems/problem_history.html', {
        'problem': problem,
        'revisions': revisions,
    })


@login_required
@require_POST
def restore_problem_revision(request, problem_id, revision_id):
    problem = get_object_or_404(Problem, id=problem_id, is_deleted=False)
    if problem.user != request.user:
        messages.error(request, "Only the problem owner can restore revisions.")
        return redirect('problem_detail', problem_id=problem.id)
    revision = get_object_or_404(ProblemRevision, id=revision_id, problem=problem)
    update_problem(problem, request.user, {
        'title': revision.title,
        'description': revision.description,
        'difficulty': revision.difficulty,
    })
    messages.success(request, f"Restored to version {revision.version}.")
    return redirect('problem_detail', problem_id=problem.id)


@login_required
@require_POST
def report_content(request):
    content_type = request.POST.get('content_type')
    object_id = request.POST.get('object_id')
    reason = request.POST.get('reason', 'other')
    description = request.POST.get('description', '')
    try:
        submit_report(request.user, content_type, int(object_id), reason, description)
        return JsonResponse({'status': 'ok', 'message': 'Report submitted.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def tag_list(request):
    query = request.GET.get('q', '')
    if query:
        tags = get_tag_suggestions(query, limit=50)
    else:
        tags = get_popular_tags(limit=50)
    return render(request, 'problems/tag_list.html', {
        'tags': tags, 'query': query,
    })


def tag_detail(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    problems = get_problems(tag=tag.name)
    return render(request, 'problems/tag_detail.html', {
        'tag': tag, 'problems': problems,
    })


def tag_autocomplete(request):
    """AJAX endpoint returning tag suggestions as JSON."""
    query = request.GET.get('q', '')
    tags = list(get_tag_suggestions(query, limit=8).values('name', 'slug', 'usage_count'))
    return JsonResponse({'tags': tags})


@login_required
def report_queue(request):
    """Admin/staff moderation queue for reports."""
    if not request.user.is_staff:
        from django.http import Http404
        raise Http404
    status_filter = request.GET.get('status', 'pending')
    if status_filter == 'resolved':
        reports = Report.objects.filter(is_resolved=True).select_related('reporter')
    else:
        reports = Report.objects.filter(is_resolved=False).select_related('reporter')
    return render(request, 'problems/report_queue.html', {
        'reports': reports,
        'status_filter': status_filter,
    })


@login_required
@require_POST
def resolve_report(request, report_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    Report.objects.filter(pk=report_id).update(is_resolved=True)
    return JsonResponse({'status': 'ok'})


# ── Helpers ────────────────────────────────────────────────────────────────

_LANGUAGE_CHOICES = [
    'Python', 'JavaScript', 'Java', 'C++', 'C', 'Go',
    'Rust', 'PHP', 'TypeScript', 'SQL', 'JSON', 'YAML',
]
