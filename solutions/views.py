from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from problems.models import Problem
from .models import Comment, Solution, Vote
from .selectors import (
    get_solution_comments,
    get_solution_revision_history,
    get_solutions_for_problem,
    get_user_voted_solution_ids,
)
from .services import (
    create_solution_revision,
    delete_comment,
    edit_comment,
    render_markdown,
    soft_delete_solution,
    toggle_solution_vote,
    update_solution,
)

# Supported languages for Monaco/Prism
_LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('javascript', 'JavaScript'),
    ('java', 'Java'),
    ('cpp', 'C++'),
    ('c', 'C'),
    ('go', 'Go'),
    ('rust', 'Rust'),
    ('php', 'PHP'),
    ('typescript', 'TypeScript'),
    ('sql', 'SQL'),
    ('json', 'JSON'),
    ('yaml', 'YAML'),
]


# ── Existing views (kept, improved with selectors) ────────────────────────


@login_required
def create_solution(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id, is_deleted=False)
    if request.method == 'POST':
        explanation = request.POST.get('explanation', '').strip()
        code = request.POST.get('code', '').strip()
        language = request.POST.get('language', 'python')
        if not explanation and not code:
            return render(request, 'solution_create.html', {
                'problem': problem,
                'error': 'Please add an explanation or code before submitting.',
                'languages': _LANGUAGE_CHOICES,
            })
        Solution.objects.create(
            user=request.user,
            problem=problem,
            explanation=explanation,
            code=code,
            language=language,
        )
        messages.success(request, 'Solution submitted successfully.')
        return redirect('problem_detail', problem_id=problem.id)
    return render(request, 'solution_create.html', {
        'problem': problem,
        'languages': _LANGUAGE_CHOICES,
    })


def solution_list(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id, is_deleted=False)
    sort = request.GET.get('sort', 'latest')
    solutions = get_solutions_for_problem(problem, sort=sort)

    user_votes = []
    if request.user.is_authenticated:
        user_votes = get_user_voted_solution_ids(request.user, solutions)

    # Render Markdown for explanations
    rendered_solutions = []
    for sol in solutions:
        rendered_solutions.append({
            'solution': sol,
            'rendered_explanation': render_markdown(sol.explanation),
            'comments': get_solution_comments(sol),
        })

    return render(request, 'solution_list.html', {
        'problem': problem,
        'rendered_solutions': rendered_solutions,
        'solutions': solutions,  # kept for backward compat
        'current_sort': sort,
        'user_votes': user_votes,
        'languages': _LANGUAGE_CHOICES,
    })


@login_required
def toggle_vote(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id, is_deleted=False)
    voted, total_votes = toggle_solution_vote(request.user, solution)
    return JsonResponse({'voted': voted, 'total_votes': total_votes})


@login_required
def accept_solution(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id, is_deleted=False)
    problem = solution.problem
    if request.user != problem.user:
        messages.error(request, 'You are not allowed to accept this solution.')
        return redirect('problem_detail', problem_id=problem.id)
    Solution.objects.filter(problem=problem, is_accepted=True).update(is_accepted=False)
    solution.is_accepted = True
    solution.save()
    # Award reputation
    try:
        from reputation.services import award_reputation
        award_reputation(solution.user, 'solution_accepted',
                         f'Solution accepted for "{problem.title}"')
    except Exception:
        pass
    messages.success(request, 'Solution accepted successfully.')
    return redirect('problem_detail', problem_id=problem.id)


@login_required
def add_comment(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id, is_deleted=False)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        parent_id = request.POST.get('parent_id')
        parent = None
        if parent_id:
            parent = Comment.objects.filter(id=parent_id, is_deleted=False).first()
        if text:
            Comment.objects.create(
                user=request.user, solution=solution, text=text, parent=parent,
            )
    return redirect('solution_list', problem_id=solution.problem_id)


# ── New views ─────────────────────────────────────────────────────────────


@login_required
def edit_solution(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id, is_deleted=False)
    if solution.user != request.user:
        messages.error(request, 'You can only edit your own solutions.')
        return redirect('solution_list', problem_id=solution.problem_id)

    if request.method == 'POST':
        data = {
            'explanation': request.POST.get('explanation', '').strip(),
            'code': request.POST.get('code', '').strip(),
            'language': request.POST.get('language', solution.language),
        }
        if not data['explanation'] and not data['code']:
            messages.error(request, 'Please provide explanation or code.')
            return redirect('edit_solution', solution_id=solution.id)
        update_solution(solution, request.user, data)
        messages.success(request, 'Solution updated.')
        return redirect('solution_list', problem_id=solution.problem_id)

    return render(request, 'solutions/solution_edit.html', {
        'solution': solution,
        'languages': _LANGUAGE_CHOICES,
    })


@login_required
@require_POST
def delete_solution(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id, is_deleted=False)
    try:
        soft_delete_solution(solution, request.user)
        messages.success(request, 'Solution deleted.')
    except PermissionError as e:
        messages.error(request, str(e))
    return redirect('solution_list', problem_id=solution.problem_id)


def solution_history(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)
    revisions = get_solution_revision_history(solution)
    return render(request, 'solutions/solution_history.html', {
        'solution': solution,
        'revisions': revisions,
    })


@login_required
@require_POST
def edit_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
    new_text = request.POST.get('text', '').strip()
    if not new_text:
        return JsonResponse({'error': 'Comment text cannot be empty.'}, status=400)
    try:
        edit_comment(comment, request.user, new_text)
        return JsonResponse({'status': 'ok', 'text': comment.text})
    except PermissionError as e:
        return JsonResponse({'error': str(e)}, status=403)


@login_required
@require_POST
def delete_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
    try:
        delete_comment(comment, request.user)
        return JsonResponse({'status': 'ok'})
    except PermissionError as e:
        return JsonResponse({'error': str(e)}, status=403)


def preview_markdown(request):
    """AJAX endpoint: render Markdown and return sanitised HTML."""
    if request.method == 'POST':
        text = request.POST.get('text', '')
        return JsonResponse({'html': render_markdown(text)})
    return JsonResponse({'error': 'POST required'}, status=405)
