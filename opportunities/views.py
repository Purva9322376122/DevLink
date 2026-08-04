from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Opportunity, Invitation, Application, Connection, Message
from .selectors import get_conversations


def opportunity_list(request):
    opportunities = Opportunity.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'opportunity_list.html', {'opportunities': opportunities})


def opportunity_detail(request, id):
    opportunity = get_object_or_404(Opportunity, id=id)
    user_application = None
    if request.user.is_authenticated:
        user_application = Application.objects.filter(
            user=request.user, opportunity=opportunity
        ).order_by('-created_at').first()
    return render(request, 'opportunity_detail.html', {
        'opportunity': opportunity,
        'user_application': user_application,
    })


@login_required
def create_opportunity(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        skills = request.POST.get('required_skills')
        Opportunity.objects.create(
            user=request.user,
            title=title,
            description=description,
            required_skills=skills,
        )
        messages.success(request, "Opportunity created successfully")
        return redirect('opportunity_list')
    return render(request, 'opportunity_create.html')


@login_required
def send_invitation(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        message = request.POST.get("message", "").strip()
        receiver = User.objects.filter(username__iexact=username).first()
        if not receiver:
            messages.error(request, "User not found")
            return redirect("invitation_list")
        if receiver == request.user:
            messages.error(request, "You cannot invite yourself")
            return redirect("invitation_list")
        Invitation.objects.create(sender=request.user, receiver=receiver, message=message)
        messages.success(request, "Invitation sent")
    return redirect("invitation_list")


@login_required
def connection_list(request):
    user = request.user

    # 1. Fetch raw connections involving user
    connection_objs = Connection.objects.filter(
        Q(user1=user) | Q(user2=user)
    ).select_related('user1', 'user2', 'user1__profile', 'user2__profile')

    connections_data = []
    my_conn_user_ids = set()
    for c in connection_objs:
        other = c.user2 if c.user1 == user else c.user1
        my_conn_user_ids.add(other.id)

    for c in connection_objs:
        other = c.user2 if c.user1 == user else c.user1
        profile = getattr(other, 'profile', None)

        # Avatar URL
        if profile and getattr(profile, 'profile_image', None):
            try:
                avatar_url = profile.profile_image.url
            except Exception:
                avatar_url = f"https://ui-avatars.com/api/?name={other.username}&background=6366f1&color=ffffff&size=120"
        else:
            avatar_url = f"https://ui-avatars.com/api/?name={other.username}&background=6366f1&color=ffffff&size=120"

        # Bio
        bio = profile.bio if profile and profile.bio else (profile.about if profile and profile.about else "")

        # Skills list
        raw_skills = profile.tech_stack if profile and profile.tech_stack else (profile.skills if profile and profile.skills else "")
        skills_list = [s.strip() for s in raw_skills.split(',') if s.strip()][:4]

        # Online status check
        is_online = False
        if other.last_login:
            time_diff = (timezone.now() - other.last_login).total_seconds()
            if time_diff < 1800:
                is_online = True
                last_active_str = "Online now"
            else:
                last_active_str = f"Active {other.last_login.strftime('%b %d')}"
        else:
            last_active_str = "Recently active"

        # Calculate mutual connections count
        other_conn_tuples = Connection.objects.filter(
            Q(user1=other) | Q(user2=other)
        ).values_list('user1_id', 'user2_id')
        other_conn_set = set()
        for u1_id, u2_id in other_conn_tuples:
            cid = u2_id if u1_id == other.id else u1_id
            if cid != user.id:
                other_conn_set.add(cid)

        mutual_count = len(my_conn_user_ids.intersection(other_conn_set))

        connections_data.append({
            'connection_id': c.id,
            'user': other,
            'username': other.username,
            'full_name': other.get_full_name() or other.username,
            'profile': profile,
            'avatar_url': avatar_url,
            'job_title': profile.job_title if profile and profile.job_title else "Software Developer",
            'location': profile.location if profile and profile.location else "Remote / Worldwide",
            'bio': bio,
            'skills': skills_list,
            'is_online': is_online,
            'last_active_str': last_active_str,
            'mutual_count': mutual_count,
            'created_at': c.created_at,
        })

    # 2. Search, Filter & Sort
    q = request.GET.get('q', '').strip().lower()
    filter_type = request.GET.get('filter', 'all').lower()
    sort_by = request.GET.get('sort', 'newest').lower()

    filtered_list = []
    for item in connections_data:
        if q:
            match_name = q in item['full_name'].lower()
            match_user = q in item['username'].lower()
            match_role = q in item['job_title'].lower()
            match_loc = q in item['location'].lower()
            match_skills = any(q in s.lower() for s in item['skills'])
            if not (match_name or match_user or match_role or match_loc or match_skills):
                continue

        if filter_type == 'online' and not item['is_online']:
            continue
        elif filter_type == 'offline' and item['is_online']:
            continue

        filtered_list.append(item)

    if sort_by == 'name':
        filtered_list.sort(key=lambda x: x['full_name'].lower())
    elif sort_by == 'active':
        filtered_list.sort(key=lambda x: x['is_online'], reverse=True)
    else:  # newest
        filtered_list.sort(key=lambda x: x['created_at'], reverse=True)

    # 3. Stats
    total_connections_count = len(connection_objs)
    online_count = sum(1 for item in connections_data if item['is_online'])
    pending_requests_count = Invitation.objects.filter(receiver=user, status='pending').count()

    if total_connections_count >= 15:
        strength_label = "Strong"
        strength_subtext = "Top 10%"
    elif total_connections_count >= 5:
        strength_label = "Strong"
        strength_subtext = "Top 15%"
    elif total_connections_count > 0:
        strength_label = "Growing"
        strength_subtext = "Top 30%"
    else:
        strength_label = "Building"
        strength_subtext = "Top 50%"

    # 4. Pagination (6 cards per page)
    paginator = Paginator(filtered_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 5. Non-connected users for Find Developers Modal
    connected_user_ids = list(my_conn_user_ids) + [user.id]
    discover_users = User.objects.exclude(id__in=connected_user_ids).select_related('profile').order_by('-date_joined')[:10]
    for d_user in discover_users:
        d_prof = getattr(d_user, 'profile', None)
        if d_prof and getattr(d_prof, 'profile_image', None):
            try:
                d_user.avatar_url = d_prof.profile_image.url
            except Exception:
                d_user.avatar_url = f"https://ui-avatars.com/api/?name={d_user.username}&background=6366f1&color=ffffff&size=80"
        else:
            d_user.avatar_url = f"https://ui-avatars.com/api/?name={d_user.username}&background=6366f1&color=ffffff&size=80"
        d_user.job_title = d_prof.job_title if d_prof and d_prof.job_title else "Developer"

    return render(request, "connection_list.html", {
        "connections": page_obj,
        "page_obj": page_obj,
        "total_connections_count": total_connections_count,
        "online_count": online_count,
        "pending_requests_count": pending_requests_count,
        "strength_label": strength_label,
        "strength_subtext": strength_subtext,
        "selected_query": q,
        "selected_filter": filter_type,
        "selected_sort": sort_by,
        "discover_users": discover_users,
    })


@login_required
def invitation_list(request):
    """Alias for connection_list to maintain backward compatibility."""
    return connection_list(request)


@login_required
def remove_connection(request, pk):
    if request.method == "POST":
        connection = get_object_or_404(Connection, id=pk)
        if request.user == connection.user1 or request.user == connection.user2:
            other_user = connection.user2 if connection.user1 == request.user else connection.user1
            connection.delete()
            messages.success(request, f"Removed connection with {other_user.username}")
        else:
            messages.error(request, "Not authorized")
    return redirect("connection_list")



@login_required
def accept_application(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if application.opportunity.user != request.user:
        messages.error(request, "Not allowed")
        return redirect('application_list')
    application.status = 'accepted'
    application.save()
    messages.success(request, "Application accepted")
    return redirect('application_list')


@login_required
def reject_application(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if application.opportunity.user != request.user:
        messages.error(request, "Not allowed")
        return redirect('application_list')
    application.status = 'rejected'
    application.save()
    messages.warning(request, "Application rejected")
    return redirect('application_list')


@login_required
def apply_opportunity(request, pk):
    opportunity = get_object_or_404(Opportunity, id=pk)
    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        github = request.POST.get("github", "").strip()
        resume = request.POST.get("resume", "").strip()
        if not message:
            messages.error(request, "Message required")
            return redirect("opportunity_detail", id=pk)
        if Application.objects.filter(user=request.user, opportunity=opportunity).exists():
            messages.warning(request, "You already applied")
            return redirect("opportunity_detail", id=pk)
        Application.objects.create(
            user=request.user,
            opportunity=opportunity,
            message=message,
            github=github,
            resume=resume,
        )
        messages.success(request, "Applied successfully!")
        return redirect("opportunity_detail", id=pk)
    return redirect("opportunity_detail", id=pk)


@login_required
def view_applications(request, pk):
    opportunity = get_object_or_404(Opportunity, id=pk, user=request.user)
    applications = Application.objects.filter(opportunity=opportunity)
    return render(request, "application_list.html", {
        "applications": applications,
        "opportunity": opportunity,
    })


@login_required
def application_list(request):
    """Opportunity owner — manages received applications."""
    applications = Application.objects.filter(
        opportunity__user=request.user
    ).select_related('user', 'opportunity').order_by('-created_at')
    return render(request, 'application_list.html', {'applications': applications})


@login_required
def applications(request):
    """Applicant — views their own submitted applications."""
    apps = Application.objects.filter(
        user=request.user
    ).select_related('opportunity').order_by('-created_at')
    return render(request, 'applications.html', {'applications': apps})


@login_required
def accept_invitation(request, pk):
    invitation = get_object_or_404(Invitation, id=pk, receiver=request.user)
    if request.method == "POST":
        invitation.status = "accepted"
        invitation.save()
        Connection.objects.get_or_create(
            user1=invitation.sender,
            user2=invitation.receiver,
        )
        messages.success(request, "You're now connected!")
    return redirect("invitation_list")


@login_required
def reject_invitation(request, pk):
    invitation = get_object_or_404(Invitation, id=pk, receiver=request.user)
    if request.method == "POST":
        invitation.status = "rejected"
        invitation.save()
        messages.warning(request, "Invitation rejected")
    return redirect("invitation_list")


@login_required
def sent_invitations(request):
    invites = Invitation.objects.filter(sender=request.user).order_by('-created_at')
    return render(request, "sent_invitations.html", {"invites": invites})


@login_required
def chat(request, username):
    other_user = get_object_or_404(User, username=username)
    is_connected = Connection.objects.filter(
        user1=request.user, user2=other_user
    ).exists() or Connection.objects.filter(
        user1=other_user, user2=request.user
    ).exists()
    if not is_connected:
        messages.error(request, "You are not connected")
        return redirect("opportunity_list")

    chat_messages = list(Message.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user],
    ).order_by("timestamp"))

    # Mark unread messages from the other user as read
    Message.objects.filter(
        sender=other_user, receiver=request.user, is_read=False
    ).update(is_read=True)

    # Enrich messages with safe sender avatar URL to avoid template attribute errors
    for msg in chat_messages:
        try:
            sender_profile = getattr(msg.sender, 'profile')
        except Exception:
            sender_profile = None
        if sender_profile and getattr(sender_profile, 'profile_image', None):
            try:
                msg.sender_profile_image_url = sender_profile.profile_image.url
            except Exception:
                msg.sender_profile_image_url = f"https://ui-avatars.com/api/?name={msg.sender.username}&background=94a3b8&color=ffffff&size=40"
        else:
            msg.sender_profile_image_url = f"https://ui-avatars.com/api/?name={msg.sender.username}&background=94a3b8&color=ffffff&size=40"

    # Prepare other_user attributes used by chat header template
    try:
        other_profile = getattr(other_user, 'profile')
    except Exception:
        other_profile = None

    other_user.profile_image_url = (other_profile.profile_image.url if other_profile and getattr(other_profile, 'profile_image', None) else f"https://ui-avatars.com/api/?name={other_user.username}&background=6366f1&color=ffffff&size=64")
    other_user.is_online = False
    # Use last_login as last_seen fallback
    other_user.last_seen = other_user.last_login
    other_user.title = other_profile.job_title if other_profile and getattr(other_profile, 'job_title', None) else ''

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content,
            )
            return redirect("chat", username=other_user.username)

    return render(request, "chat.html", {
        "messages": chat_messages,
        "other_user": other_user,
    })


@login_required
def messages_list(request):
    conversations = get_conversations(request.user)
    return render(request, "messages_list.html", {"conversations": conversations})
