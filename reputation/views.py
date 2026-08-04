from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .selectors import get_reputation_history, get_user_badges, get_leaderboard
from .services import get_user_level
from .models import LEVEL_THRESHOLDS


@login_required
def reputation_view(request):
    history = get_reputation_history(request.user)
    badges = get_user_badges(request.user)
    level = get_user_level(request.user)

    # Calculate progress to next level
    try:
        score = request.user.profile.reputation_score
    except Exception:
        score = 0

    next_threshold = None
    current_threshold = 0
    for threshold, name in LEVEL_THRESHOLDS:
        if score >= threshold:
            current_threshold = threshold
        else:
            next_threshold = threshold
            break

    progress = 0
    if next_threshold:
        span = next_threshold - current_threshold
        gained = score - current_threshold
        progress = int((gained / span) * 100) if span > 0 else 0

    return render(request, 'reputation/reputation.html', {
        'history': history,
        'badges': badges,
        'level': level,
        'score': score,
        'next_threshold': next_threshold,
        'progress': progress,
    })


@login_required
def leaderboard_view(request):
    leaderboard = get_leaderboard(limit=20)
    from .models import get_level_for_score
    leaderboard_data = [
        {
            'rank': i + 1,
            'profile': entry,
            'level': get_level_for_score(entry.reputation_score),
        }
        for i, entry in enumerate(leaderboard)
    ]
    return render(request, 'reputation/leaderboard.html', {
        'leaderboard': leaderboard_data,
    })
