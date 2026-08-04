# Design Document — DevLink v1.0

> Feature: `devlink-v1`
> Workflow: Requirements-First
> Last Updated: 2025

---

## Part 1: System Architecture

### 1.1 High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│   Browser (Bootstrap 5 + Vanilla JS + WebSocket)                    │
└───────────┬─────────────────────────────────┬───────────────────────┘
            │ HTTP/HTTPS                       │ WSS
            ▼                                 ▼
┌───────────────────────┐       ┌─────────────────────────┐
│    Nginx (Reverse      │       │  Nginx → Daphne (ASGI)  │
│    Proxy + Static)     │       │  WebSocket Upgrade      │
└───────────┬────────────┘       └──────────┬──────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌─────────────────────────┐
│  Gunicorn (WSGI)       │       │  Django Channels ASGI    │
│  Django Views / DRF    │       │  Consumers               │
└───────────┬────────────┘       └──────────┬──────────────┘
            │                               │
            └──────────────┬────────────────┘
                           ▼
            ┌──────────────────────────┐
            │     Django Application    │
            │  ┌────────────────────┐  │
            │  │  Service Layer      │  │
            │  │  Selector Layer     │  │
            │  └─────────┬──────────┘  │
            │            │             │
            │  ┌─────────▼──────────┐  │
            │  │    ORM / Models     │  │
            │  └─────────┬──────────┘  │
            └────────────┼─────────────┘
                         │
           ┌─────────────┴──────────────┐
           │                            │
           ▼                            ▼
┌──────────────────┐        ┌───────────────────────┐
│   PostgreSQL      │        │  Redis                 │
│   (Primary DB)    │        │  - Channel Layer       │
└──────────────────┘        │  - Celery Broker        │
                             └───────────┬────────────┘
                                         │
                             ┌───────────▼────────────┐
                             │  Celery Worker + Beat   │
                             │  (Background Tasks)     │
                             └────────────────────────┘
```

### 1.2 Component Breakdown — Django Apps and Responsibilities

| App | Responsibility |
|-----|---------------|
| `accounts` | User registration, login/logout, profile management, follow system, login history, email verification, password reset |
| `problems` | Problem CRUD, tag management, view count tracking, attachments, categories, bookmarks on problems |
| `solutions` | Solution CRUD, voting (up/down), accept, edit history, bookmarks on solutions |
| `opportunities` | Opportunity CRUD, application management, invitation system, connection management, bookmarks on opportunities |
| `notifications` | Notification model, WebSocket consumer, signal handlers, notification center views |
| `bookmarks` | Generic bookmark model, bookmark/unbookmark views, bookmark list views |
| `reputation` | Reputation score tracking, level calculation, badge award logic, reputation history |
| `search` | Global search view, search API endpoint, autocomplete endpoint |
| `core` | Shared utilities (mixins, validators, pagination, error handlers, audit logging, base service/selector classes) |
| `api` | DRF router configuration, API-level middleware, drf-spectacular schema hooks |

### 1.3 Request/Response Flow

#### Web UI Request (Session Auth)

```
Browser GET /problems/
  → Nginx (static check, proxy to Gunicorn)
    → Django URL Router → problems/urls.py
      → ProblemListView (LoginRequiredMixin)
        → selector: get_problems_queryset(filters, user)
          → ORM query with select_related/prefetch_related
        → Template render: problem_list.html extends base.html
      ← HttpResponse (HTML)
    ← Gunicorn response
  ← Nginx response
← Browser renders HTML
```

#### API Request (JWT Auth)

```
Client POST /api/v1/problems/ + Authorization: Bearer <token>
  → Nginx proxy
    → Gunicorn → Django DRF Router
      → JWTAuthentication.authenticate()
        → Validate token, fetch user
      → ProblemViewSet.create()
        → IsAuthenticated permission check
        → ProblemWriteSerializer.validate()
        → service: create_problem(user, validated_data)
          → Problem.objects.create(...)
          → ReputationService.award(user, 'problem_posted')
        ← 201 Created + ProblemReadSerializer(problem).data
      ← JSON response
    ← Gunicorn
  ← Nginx
← Client
```

#### WebSocket Connection Flow

```
Browser → WSS /ws/chat/other_user/
  → Nginx (Upgrade: websocket header)
    → Daphne ASGI server
      → Django Channels Router → ChatConsumer
        → connect(): JWT or session token auth
        → accept()
        → Group: chat_{min_id}_{max_id}
        → Receive loop: process events
        → disconnect(): leave group, update last_seen
```

### 1.4 Layer Architecture

The application follows a strict layered architecture:

```
URL Router
    ↓
Views / ViewSets / Consumers
    ↓
Permissions (IsOwner, IsAuthenticated, IsConnected, IsPublic)
    ↓
Services (business logic, mutations, side-effects)
    ↓
Selectors (read-only queries, no mutations)
    ↓
Models / ORM
    ↓
Database (PostgreSQL / SQLite)
```

**Rules:**
- Views call services and selectors — never raw ORM queries directly.
- Services may call selectors, but selectors never call services.
- Cross-app logic is handled via Django signals (e.g., awarding reputation after a vote).
- No direct cross-app model imports in service layers — use signal dispatch instead.

### 1.5 Django App Module Structure

Each app contains the following modules (create as needed per app):

```
app_name/
├── __init__.py
├── apps.py
├── admin.py          # ModelAdmin registrations
├── models.py         # Django ORM models
├── views.py          # Class-based and function-based views
├── urls.py           # URL patterns
├── forms.py          # Django forms (web UI)
├── services.py       # Business logic functions (mutations)
├── selectors.py      # Query functions (reads only)
├── permissions.py    # DRF permission classes
├── serializers.py    # DRF serializers
├── signals.py        # Django signal handlers
├── validators.py     # Custom field/model validators
├── consumers.py      # Django Channels WebSocket consumers
├── tasks.py          # Celery tasks
├── tests.py          # Unit + property-based tests
└── migrations/
```

### 1.6 New Apps to Create

- `notifications` — Notification model + NotificationConsumer + signal wiring
- `bookmarks` — Generic FK bookmark model + views + API
- `reputation` — ReputationEvent model + badge system + services
- `search` — Unified search views + DRF endpoint
- `core` — Shared base classes, mixins, validators, audit logging
- `api` — DRF router, schema configuration, API-wide middleware

### 1.7 Apps to Refactor

- `accounts` — Add: `Follow`, `LoginEvent`, extended `Profile` fields, email verification, password reset
- `opportunities` — Add: `opportunity_type`, `deadline`, application file upload, invitation enhancements
- `problems` — Add: `ProblemView`, `ProblemAttachment`, `category` field, edit/delete views
- `solutions` — Add: `SolutionEditHistory`, `CommentReaction`, downvote extension to `Vote`, pinned comments

---

## Part 2: Database Schema & ER Overview

### 2.1 Existing Models — Extensions

#### `accounts.Profile` (extended)

```python
class Profile(models.Model):
    user              = models.OneToOneField(User, on_delete=models.CASCADE)
    # --- existing fields ---
    bio               = models.TextField(blank=True)
    skills            = models.CharField(max_length=255, blank=True)
    profile_image     = models.ImageField(upload_to='profiles/', blank=True)
    github            = models.URLField(blank=True)
    linkedin          = models.URLField(blank=True)
    # --- new fields ---
    full_name         = models.CharField(max_length=150, blank=True)
    cover_photo       = models.ImageField(upload_to='covers/', blank=True, null=True)
    location          = models.CharField(max_length=100, blank=True)
    experience_level  = models.CharField(
                            max_length=20,
                            choices=[('junior','Junior'),('mid','Mid'),('senior','Senior'),('lead','Lead')],
                            blank=True)
    languages         = models.CharField(max_length=255, blank=True)   # comma-separated spoken languages
    tech_stack        = models.CharField(max_length=500, blank=True)   # comma-separated technologies
    portfolio         = models.URLField(blank=True)
    resume            = models.FileField(upload_to='resumes/', blank=True, null=True)
    availability_status = models.CharField(
                            max_length=20,
                            choices=[('available','Available'),('busy','Busy'),('open','Open to Work')],
                            default='available')
    about             = models.TextField(blank=True)
    reputation_score  = models.IntegerField(default=0, db_index=True)

    class Meta:
        indexes = [models.Index(fields=['reputation_score'])]
```

#### `problems.Problem` (extended)

```python
class Problem(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problems')
    title       = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    difficulty  = models.CharField(max_length=10, choices=[...], default='easy', db_index=True)
    tags        = models.ManyToManyField('Tag', blank=True)
    # --- new fields ---
    category    = models.CharField(max_length=100, blank=True, db_index=True)
    view_count  = models.PositiveIntegerField(default=0, db_index=True)
    is_deleted  = models.BooleanField(default=False)   # soft delete
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['difficulty', 'created_at']),
            models.Index(fields=['category', 'created_at']),
        ]
```

#### `solutions.Solution` (extended)

```python
class Solution(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solutions')
    problem     = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solutions')
    explanation = models.TextField()
    code        = models.TextField(blank=True, null=True)
    is_accepted = models.BooleanField(default=False, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['problem', 'is_accepted', '-created_at'])]
```

#### `solutions.Vote` (extended)

```python
class Vote(models.Model):
    VOTE_TYPES = [('upvote', 'Upvote'), ('downvote', 'Downvote')]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    solution    = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='votes')
    vote_type   = models.CharField(max_length=10, choices=VOTE_TYPES, default='upvote')  # NEW
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'solution')   # enforced at DB level
        indexes = [models.Index(fields=['solution', 'vote_type'])]
```

#### `solutions.Comment` (extended)

```python
class Comment(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    solution    = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='comments')
    text        = models.TextField(max_length=2000)
    parent      = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_pinned   = models.BooleanField(default=False)  # NEW
    is_edited   = models.BooleanField(default=False)  # NEW
    edited_at   = models.DateTimeField(null=True, blank=True)  # NEW
    created_at  = models.DateTimeField(auto_now_add=True)
```

#### `opportunities.Opportunity` (extended)

```python
class Opportunity(models.Model):
    OPPORTUNITY_TYPES = [
        ('job', 'Job'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
        ('open_source', 'Open Source'),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opportunities')
    title           = models.CharField(max_length=255, db_index=True)
    description     = models.TextField()
    required_skills = models.CharField(max_length=255)
    is_active       = models.BooleanField(default=True, db_index=True)
    # --- new fields ---
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES, default='job', db_index=True)
    deadline         = models.DateField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['opportunity_type', 'is_active', '-created_at'])]
```

#### `opportunities.Application` (extended)

```python
class Application(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')]

    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    opportunity     = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='applications')
    message         = models.TextField()
    github          = models.URLField(blank=True, null=True)
    resume_url      = models.URLField(blank=True, null=True)   # legacy URL field
    resume_file     = models.FileField(upload_to='resumes/', blank=True, null=True)  # NEW file upload
    portfolio       = models.URLField(blank=True, null=True)   # NEW
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'opportunity')
```

#### `opportunities.Message` (extended)

```python
class Message(models.Model):
    sender      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content     = models.TextField(blank=True)
    file_url    = models.URLField(blank=True, null=True)   # NEW
    file_type   = models.CharField(max_length=20, blank=True)  # NEW: 'image' | 'file'
    timestamp   = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read     = models.BooleanField(default=False, db_index=True)
    is_delivered = models.BooleanField(default=False)   # NEW
    is_pinned   = models.BooleanField(default=False)    # NEW

    class Meta:
        indexes = [
            models.Index(fields=['sender', 'receiver', 'timestamp']),
            models.Index(fields=['receiver', 'is_read']),
        ]
```

---

### 2.2 New Models

#### `accounts.Follow`

```python
class Follow(models.Model):
    follower    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F('following')),
                name='no_self_follow'
            )
        ]
```

#### `accounts.LoginEvent`

```python
class LoginEvent(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_events')
    ip_address  = models.GenericIPAddressField()
    user_agent  = models.TextField()
    session_key = models.CharField(max_length=40, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['user', '-timestamp'])]
```

#### `notifications.Notification`

```python
class Notification(models.Model):
    VERB_CHOICES = [
        ('connection_request', 'Connection Request'),
        ('connection_accepted', 'Connection Accepted'),
        ('solution_commented', 'Solution Commented'),
        ('solution_accepted', 'Solution Accepted'),
        ('solution_upvoted', 'Solution Upvoted'),
        ('solution_downvoted', 'Solution Downvoted'),
        ('comment_replied', 'Comment Replied'),
        ('message_received', 'Message Received'),
        ('application_accepted', 'Application Accepted'),
        ('application_rejected', 'Application Rejected'),
    ]

    recipient   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='acted_notifications')
    verb        = models.CharField(max_length=30, choices=VERB_CHOICES, db_index=True)
    # Generic FK for the target object
    content_type  = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id     = models.PositiveIntegerField(null=True, blank=True)
    target_url    = models.CharField(max_length=500, blank=True)
    is_read       = models.BooleanField(default=False, db_index=True)
    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]
```

#### `bookmarks.Bookmark`

```python
class Bookmark(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id    = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [models.Index(fields=['user', 'content_type'])]
```

#### `reputation.ReputationEvent`

```python
class ReputationEvent(models.Model):
    EVENT_TYPES = [
        ('solution_upvoted', '+10'),
        ('solution_downvoted', '-2'),
        ('solution_accepted', '+25'),
        ('problem_posted', '+5'),
        ('comment_posted', '+2'),
        ('connection_established', '+5'),
        ('upvote_removed', '-10'),
        ('downvote_removed', '+2'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reputation_events')
    event_type  = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    delta       = models.IntegerField()
    description = models.CharField(max_length=200, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]
```

#### `reputation.Badge`

```python
class Badge(models.Model):
    TRIGGER_CHOICES = [
        ('first_solution', 'First Solution'),
        ('problem_solver', '10 Accepted Solutions'),
        ('community_builder', '50 Connections'),
        ('upvote_magnet', '100 Upvotes Received'),
        ('top_contributor', 'Expert Level'),
    ]

    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True)
    description = models.TextField()
    icon        = models.CharField(max_length=50)   # Bootstrap Icons class, e.g. 'bi-award'
    trigger     = models.CharField(max_length=30, choices=TRIGGER_CHOICES, unique=True)

class UserBadge(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge       = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
```

#### `problems.ProblemView`

```python
class ProblemView(models.Model):
    problem     = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='problem_views')
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    viewed_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent double-counting same user on same day
        indexes = [models.Index(fields=['problem', 'user']),
                   models.Index(fields=['problem', 'ip_address'])]
```

#### `problems.ProblemAttachment`

```python
class ProblemAttachment(models.Model):
    problem     = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='attachments')
    file        = models.ImageField(upload_to='problem_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

#### `solutions.SolutionEditHistory`

```python
class SolutionEditHistory(models.Model):
    solution    = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='edit_history')
    editor      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    explanation = models.TextField()
    code        = models.TextField(blank=True)
    edited_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-edited_at']
```

#### `solutions.CommentReaction`

```python
class CommentReaction(models.Model):
    REACTION_TYPES = [
        ('thumbs_up', '👍'),
        ('heart', '❤️'),
        ('laugh', '😄'),
        ('celebrate', '🎉'),
        ('wow', '😮'),
        ('sad', '😢'),
    ]

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_reactions')
    comment       = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=15, choices=REACTION_TYPES)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment', 'reaction_type')
```

#### `opportunities.ChatFile`

```python
class ChatFile(models.Model):
    message     = models.OneToOneField(Message, on_delete=models.CASCADE, related_name='chat_file')
    file        = models.FileField(upload_to='chat_files/')
    file_type   = models.CharField(max_length=10, choices=[('image','Image'),('file','File')])
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

#### `opportunities.PinnedMessage`

```python
class PinnedMessage(models.Model):
    # Identifies conversation by the sorted user pair
    conversation_key = models.CharField(max_length=50, db_index=True)  # e.g. "42_99"
    message          = models.ForeignKey(Message, on_delete=models.CASCADE)
    pinned_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pinned_at        = models.DateTimeField(auto_now_add=True)
```

#### `core.AuditLog`

```python
class AuditLog(models.Model):
    EVENT_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Login Failed'),
        ('account_activated', 'Account Activated'),
        ('password_reset', 'Password Reset'),
        ('account_deactivated', 'Account Deactivated'),
        ('content_deleted', 'Content Deleted'),
        ('permission_denied', 'Permission Denied'),
    ]

    user          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type    = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id   = models.CharField(max_length=50, blank=True)
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    user_agent    = models.TextField(blank=True)
    description   = models.TextField(blank=True)
    timestamp     = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
```

---

### 2.3 Relationships Summary

```
User ──< Profile (1:1)
User ──< Problem (1:N, via user FK)
User ──< Solution (1:N)
User ──< Vote (1:N)
User ──< Comment (1:N)
User ──< Opportunity (1:N)
User ──< Application (1:N)
User ──< Message (1:N sender, 1:N receiver)
User ──< Follow (1:N follower, 1:N following)
User ──< Notification (1:N recipient)
User ──< Bookmark (1:N)
User ──< ReputationEvent (1:N)
User ──< UserBadge (1:N)
User ──< LoginEvent (1:N)

Problem >──< Tag (M2M)
Problem ──< Solution (1:N)
Problem ──< ProblemView (1:N)
Problem ──< ProblemAttachment (1:N)

Solution ──< Vote (1:N)
Solution ──< Comment (1:N)
Solution ──< SolutionEditHistory (1:N)

Comment ──< Comment (self-referential parent/replies 1:N)
Comment ──< CommentReaction (1:N)

Message ──< ChatFile (1:1 optional)

Invitation (sender FK User, receiver FK User)
Connection (user1 FK User, user2 FK User)

Bookmark → ContentType + object_id (Generic FK to Problem | Solution | Opportunity)
Notification → ContentType + object_id (Generic FK to any target resource)
```

---

### 2.4 Database Optimization Notes

- **select_related**: Use on all FK fields fetched in list views (e.g., `Problem.objects.select_related('user__profile')`, `Solution.objects.select_related('user__profile', 'problem')`).
- **prefetch_related**: Use for M2M and reverse FK (e.g., `Problem.objects.prefetch_related('tags', 'solutions')`, `Solution.objects.prefetch_related('votes', 'comments')`).
- **Indexes**: All `db_index=True` fields listed above. Composite indexes on commonly co-filtered fields (e.g., `[difficulty, created_at]`, `[opportunity_type, is_active, -created_at]`).
- **View count updates**: Use `F()` expressions — `Problem.objects.filter(pk=pk).update(view_count=F('view_count') + 1)` — to avoid race conditions.
- **Reputation updates**: Wrapped in `transaction.atomic()` to prevent concurrent update conflicts.
- **Bookmark counts**: Use `Count('bookmarks')` annotation on querysets rather than a stored counter field to stay consistent.

---

## Part 3: Authentication & Security Design

### 3.1 Session Authentication Flow (Web UI)

```
1. User submits POST /accounts/login/ with {username_or_email, password, remember_me}
2. CustomAuthBackend.authenticate() — tries User.objects.get(username=identifier)
   then falls back to User.objects.get(email=identifier)
3. If credentials valid AND user.is_active:
   a. django.contrib.auth.login(request, user)  → creates session record
   b. If remember_me: request.session.set_expiry(30 * 24 * 3600)
      Else: request.session.set_expiry(0)  (browser session)
   c. LoginEvent.objects.create(user, ip, user_agent, session_key)
   d. AuditLog.objects.create(event_type='login', user, ip)
   e. Redirect → dashboard
4. If credentials invalid:
   a. rate_limiter.record_failure(ip)
   b. If failures >= 5 within 10 min: block IP for 15 min, return 429
   c. Return form with generic error (no field-level hint)
```

The custom authentication backend (`accounts/backends.py`) allows login with both `username` and `email`:

```python
class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```

### 3.2 JWT Authentication Flow (API)

```
1. POST /api/auth/token/ with {username, password}
   → TokenObtainPairView (SimpleJWT)
   → Returns: {access: <JWT, 60min>, refresh: <JWT, 7days>}

2. Client stores tokens (memory or httpOnly cookie — never localStorage for access token)

3. Authenticated API request:
   GET /api/v1/problems/ + Header: Authorization: Bearer <access_token>
   → JWTAuthentication.authenticate(request)
   → Decode token → validate exp → fetch User from user_id claim
   → request.user = user

4. Token refresh:
   POST /api/auth/token/refresh/ with {refresh: <token>}
   → Returns new {access: <JWT>}
   → Old refresh token is rotated (ROTATE_REFRESH_TOKENS = True)
   → Old refresh token is blacklisted (BLACKLIST_AFTER_ROTATION = True)
```

**SimpleJWT settings** (in `settings/base.py`):
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

### 3.3 Email Verification Flow

```
1. POST /accounts/signup/ with {username, email, password1, password2}
   → Validate form → User.objects.create_user(..., is_active=False)
   → Profile auto-created via post_save signal
   → tasks.send_activation_email.delay(user.id)
      → Celery worker:
         token = account_activation_token.make_token(user)  # django PasswordResetTokenGenerator
         uid = urlsafe_base64_encode(force_bytes(user.pk))
         url = f"/accounts/activate/{uid}/{token}/"
         send HTML email via Django's send_mail

2. GET /accounts/activate/<uidb64>/<token>/
   → Decode uid → fetch User
   → account_activation_token.check_token(user, token)
   → If valid AND token < 24h old:
      user.is_active = True; user.save()
      Redirect → /accounts/login/ with success message
   → If expired:
      Render activation_expired.html with resend link
```

### 3.4 Password Reset Flow

```
1. POST /accounts/forgot-password/ with {email}
   → Always return same "check your email" response (no enumeration)
   → tasks.send_password_reset_email.delay(email)
      → Celery:
         try: user = User.objects.get(email=email)
         token = default_token_generator.make_token(user)
         uid = urlsafe_base64_encode(force_bytes(user.pk))
         send email with /accounts/reset-password/<uid>/<token>/

2. GET /accounts/reset-password/<uidb64>/<token>/
   → Validate token (1-hour expiry via default_token_generator)
   → Render password_reset_confirm.html

3. POST /accounts/reset-password/<uidb64>/<token>/ with {new_password1, new_password2}
   → Validate strength policy
   → user.set_password(new_password1); user.save()
   → flush all sessions: request.session.flush()
   → AuditLog password_reset event
   → Redirect → login with success message
```

### 3.5 RBAC Permission Design

Four DRF permission classes in `core/permissions.py`:

```python
class IsOwnerOrReadOnly(BasePermission):
    """Write access only to the object owner."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user

class IsOwner(BasePermission):
    """Full access only to the object owner. No read for others."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsConnected(BasePermission):
    """Access only if requester is connected (has Connection) to the target user."""
    def has_permission(self, request, view):
        target_username = view.kwargs.get('username')
        if not target_username:
            return False
        return Connection.objects.filter(
            models.Q(user1=request.user, user2__username=target_username) |
            models.Q(user2=request.user, user1__username=target_username)
        ).exists()

class IsPublic(BasePermission):
    """Read-only public access."""
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
```

Permission matrix per resource:

| Resource | List/Retrieve | Create | Update/Delete |
|----------|--------------|--------|---------------|
| Profile | Public | N/A | IsOwner |
| Problem | Public | IsAuthenticated | IsOwner |
| Solution | Public | IsAuthenticated | IsOwner |
| Comment | Public | IsAuthenticated | IsOwner |
| Vote | — | IsAuthenticated, not owner | IsOwner |
| Opportunity | Public | IsAuthenticated | IsOwner |
| Application | IsOwner | IsAuthenticated | IsOwner (withdraw) |
| Message | IsConnected | IsConnected | — |
| Notification | IsOwner | — | IsOwner |
| Bookmark | IsOwner | IsAuthenticated | IsOwner |

### 3.6 Rate Limiting Design

Rate limiting is implemented via a custom middleware `core/middleware.py` using Redis for counter storage.

```python
class RateLimitMiddleware:
    """
    Applies rate limits per path prefix.
    - Auth endpoints: 5 requests per IP per 10-minute window
    - API authenticated: 100 requests per user per minute
    - API unauthenticated: 20 requests per IP per minute
    """
    RATE_RULES = [
        (r'^/api/auth/', 5, 600, 'ip'),         # 5/10min on auth
        (r'^/accounts/login/', 5, 600, 'ip'),
        (r'^/accounts/forgot-password/', 5, 600, 'ip'),
        (r'^/api/', 100, 60, 'user'),            # 100/min authenticated
        (r'^/api/', 20, 60, 'ip'),               # 20/min unauthenticated
    ]
```

The middleware uses Redis `INCR` + `EXPIRE` pattern:
```
key = f"rl:{rule_type}:{identifier}:{endpoint_prefix}"
count = redis_client.incr(key)
if count == 1: redis_client.expire(key, window_seconds)
if count > limit: return HttpResponse(status=429)
```

### 3.7 Security Headers Middleware

`core/middleware.py` — `SecurityHeadersMiddleware`:

```python
class SecurityHeadersMiddleware:
    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        # CSP set in production settings via django-csp or manually
        return response
```

Production CSP (in `settings/production.py`):
```
Content-Security-Policy: default-src 'self';
  script-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com;
  style-src 'self' 'unsafe-inline' cdn.jsdelivr.net;
  img-src 'self' data: ui-avatars.com;
  connect-src 'self' wss://devlink.example.com;
  font-src 'self' cdn.jsdelivr.net;
  frame-ancestors 'none';
```

### 3.8 File Upload Validation Pipeline

All file uploads go through `core/validators.py`:

```python
class FileValidator:
    ALLOWED_IMAGE_MIMES = {'image/jpeg', 'image/png', 'image/webp'}
    ALLOWED_RESUME_MIMES = {'application/pdf'}
    ALLOWED_CHAT_MIMES = {'image/jpeg', 'image/png', 'image/webp',
                           'application/pdf', 'text/plain'}

    @staticmethod
    def validate_image(file, max_mb=5):
        mime = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)
        if mime not in FileValidator.ALLOWED_IMAGE_MIMES:
            raise ValidationError(f"Unsupported image type: {mime}")
        if file.size > max_mb * 1024 * 1024:
            raise ValidationError(f"Image must be under {max_mb}MB")

    @staticmethod
    def sanitize_filename(name):
        return re.sub(r'[^\w\s\-.]', '', name)[:100]
```

### 3.9 Audit Logging Design

`core/services.py` — `AuditService`:

```python
def log_event(event_type, request=None, user=None, resource_type='', resource_id='', description=''):
    AuditLog.objects.create(
        user=user or (request.user if request and request.user.is_authenticated else None),
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
        description=description,
    )
```

Triggered on: login, logout, login failure, password reset, account activation, account deactivation by admin, content deletion by admin, and all 403 permission denied events.

---

## Part 4: API Design

### 4.1 Base URL and Versioning

All API endpoints are prefixed with `/api/v1/`. Auth token endpoints live at `/api/auth/`.

```
/api/auth/token/           POST   Obtain JWT access + refresh token
/api/auth/token/refresh/   POST   Refresh access token
/api/docs/                 GET    Swagger UI (drf-spectacular)
/api/redoc/                GET    ReDoc documentation
/api/schema/               GET    Raw OpenAPI 3.0 JSON schema
```

### 4.2 Resource Endpoints

#### Profiles

```
GET    /api/v1/profiles/                    List all profiles (public, paginated)
GET    /api/v1/profiles/<username>/         Retrieve a profile by username
PATCH  /api/v1/profiles/<username>/         Update own profile (IsOwner)
POST   /api/v1/profiles/<username>/follow/  Follow a user (IsAuthenticated)
DELETE /api/v1/profiles/<username>/follow/  Unfollow a user (IsAuthenticated)
GET    /api/v1/profiles/<username>/followers/   List followers
GET    /api/v1/profiles/<username>/following/   List following
```

#### Problems

```
GET    /api/v1/problems/                    List problems (public, paginated)
POST   /api/v1/problems/                    Create problem (IsAuthenticated)
GET    /api/v1/problems/<id>/               Retrieve problem detail
PUT    /api/v1/problems/<id>/               Full update own problem (IsOwner)
PATCH  /api/v1/problems/<id>/               Partial update own problem (IsOwner)
DELETE /api/v1/problems/<id>/               Soft-delete own problem (IsOwner)
POST   /api/v1/problems/<id>/bookmark/      Bookmark a problem
DELETE /api/v1/problems/<id>/bookmark/      Remove bookmark
```

Query params on `GET /api/v1/problems/`:
- `q` — full-text search on title + description
- `difficulty` — easy | medium | hard
- `tag` — tag name
- `category` — category string
- `ordering` — created_at | -created_at | view_count | -view_count (default: `-created_at`)
- `page`, `page_size`

#### Solutions

```
GET    /api/v1/problems/<id>/solutions/             List solutions for a problem
POST   /api/v1/problems/<id>/solutions/             Create solution (IsAuthenticated)
GET    /api/v1/solutions/<id>/                      Retrieve solution detail
PUT    /api/v1/solutions/<id>/                      Update own solution (IsOwner)
DELETE /api/v1/solutions/<id>/                      Delete own solution (IsOwner)
POST   /api/v1/solutions/<id>/vote/                 Cast/toggle vote (IsAuthenticated)
POST   /api/v1/solutions/<id>/accept/               Accept solution (Problem owner only)
POST   /api/v1/solutions/<id>/bookmark/             Bookmark a solution
DELETE /api/v1/solutions/<id>/bookmark/             Remove bookmark
GET    /api/v1/solutions/<id>/history/              Edit history (IsAuthenticated)
```

Vote endpoint request body: `{"vote_type": "upvote" | "downvote"}`
Vote endpoint response: `{"vote_count": 12, "user_vote": "upvote" | "downvote" | null}`

#### Comments

```
GET    /api/v1/solutions/<id>/comments/             List top-level comments
POST   /api/v1/solutions/<id>/comments/             Create comment (IsAuthenticated)
PATCH  /api/v1/comments/<id>/                       Edit own comment (IsOwner)
DELETE /api/v1/comments/<id>/                       Delete own comment (IsOwner)
POST   /api/v1/comments/<id>/react/                 Add/toggle reaction (IsAuthenticated)
POST   /api/v1/comments/<id>/pin/                   Pin comment (Problem owner only)
```

React request body: `{"reaction_type": "thumbs_up" | "heart" | "laugh" | "celebrate" | "wow" | "sad"}`

#### Opportunities

```
GET    /api/v1/opportunities/                       List opportunities (public, paginated)
POST   /api/v1/opportunities/                       Create opportunity (IsAuthenticated)
GET    /api/v1/opportunities/<id>/                  Retrieve detail
PUT    /api/v1/opportunities/<id>/                  Update own opportunity (IsOwner)
DELETE /api/v1/opportunities/<id>/                  Soft-delete (is_active=False) (IsOwner)
POST   /api/v1/opportunities/<id>/apply/            Apply to opportunity (IsAuthenticated)
POST   /api/v1/opportunities/<id>/bookmark/         Bookmark
DELETE /api/v1/opportunities/<id>/bookmark/         Remove bookmark
GET    /api/v1/opportunities/<id>/applications/     List applications (IsOwner of opportunity)
PATCH  /api/v1/applications/<id>/                   Accept or reject application (IsOwner of opportunity)
DELETE /api/v1/applications/<id>/                   Withdraw application (IsOwner of application)
```

Query params on `GET /api/v1/opportunities/`:
- `q` — search title + description + required_skills
- `type` — job | internship | freelance | open_source
- `is_active` — true | false
- `ordering` — created_at | -created_at | -applications_count

#### Connections & Invitations

```
GET    /api/v1/connections/                         List own connections
DELETE /api/v1/connections/<id>/                    Remove connection (IsOwner)
GET    /api/v1/invitations/                         List received + sent invitations
POST   /api/v1/invitations/                         Send invitation (IsAuthenticated)
PATCH  /api/v1/invitations/<id>/                    Accept or reject invitation (IsOwner=receiver)
DELETE /api/v1/invitations/<id>/                    Cancel sent invitation (IsOwner=sender)
GET    /api/v1/connections/suggestions/             Suggested developers (IsAuthenticated)
```

#### Notifications

```
GET    /api/v1/notifications/                       List notifications (IsAuthenticated)
PATCH  /api/v1/notifications/<id>/                  Mark single notification as read
POST   /api/v1/notifications/mark-all-read/         Mark all as read
DELETE /api/v1/notifications/<id>/                  Delete notification
```

#### Bookmarks

```
GET    /api/v1/bookmarks/                           List all bookmarks grouped by type
DELETE /api/v1/bookmarks/<id>/                      Remove bookmark
```

#### Search

```
GET    /api/v1/search/                              Unified search
GET    /api/v1/search/autocomplete/                 Autocomplete suggestions (2+ chars)
```

Query params on `/api/v1/search/`:
- `q` — required, 1+ characters
- `type` — developer | problem | solution | opportunity (optional, returns all if omitted)
- `ordering` — relevance | newest

#### Reputation

```
GET    /api/v1/reputation/history/                  Reputation event history (IsAuthenticated)
```

### 4.3 Pagination Design

All list endpoints use `PageNumberPagination`:

```python
class DevLinkPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
```

### 4.4 Serializer Design Principles

- **Read vs Write serializers**: Use separate `*ReadSerializer` (nested, rich) and `*WriteSerializer` (flat, validated) classes for each resource to avoid write-side complexity.
- **Nested serializers**: Profile info nested into Problem, Solution, etc. via `UserMiniSerializer` with only `{id, username, profile_image_url}`.
- **Computed fields**: `vote_count`, `solution_count`, `bookmark_count`, `is_bookmarked` (request-user-specific), `user_vote` added as `SerializerMethodField`.
- **Validation**: Cross-field validators in `validate()` method; never in views.

Example:

```python
class ProblemReadSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(source='user', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    solution_count = serializers.IntegerField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = ['id', 'author', 'title', 'description', 'difficulty',
                  'category', 'tags', 'view_count', 'solution_count',
                  'is_bookmarked', 'created_at']

class ProblemWriteSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField(), max_length=5)

    class Meta:
        model = Problem
        fields = ['title', 'description', 'difficulty', 'category', 'tags']

    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value
```

### 4.5 Error Response Format

All API errors return a consistent JSON body:

```json
{
  "error": "Human-readable message",
  "code": "machine_readable_code",
  "details": {}
}
```

HTTP status codes used:
- `200` — Successful read
- `201` — Successful create
- `204` — Successful delete
- `400` — Validation error (details contains field errors)
- `401` — Authentication required
- `403` — Permission denied
- `404` — Resource not found
- `429` — Rate limit exceeded

Custom exception handler in `core/exceptions.py`:

```python
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'error': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'code': getattr(exc, 'default_code', 'error'),
            'details': response.data if isinstance(response.data, dict) else {},
        }
    return response
```

### 4.6 drf-spectacular Configuration

```python
# settings/base.py
SPECTACULAR_SETTINGS = {
    'TITLE': 'DevLink API',
    'DESCRIPTION': 'Developer networking platform REST API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication endpoints'},
        {'name': 'profiles', 'description': 'User profile management'},
        {'name': 'problems', 'description': 'Technical problems'},
        {'name': 'solutions', 'description': 'Problem solutions'},
        {'name': 'opportunities', 'description': 'Job and collaboration opportunities'},
        {'name': 'notifications', 'description': 'Real-time notifications'},
        {'name': 'search', 'description': 'Global search'},
        {'name': 'reputation', 'description': 'Reputation and badges'},
    ],
}
```

---

## Part 5: WebSocket & Real-Time Design

### 5.1 Django Channels Routing

`Connect/routing.py` (project-level):

```python
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from core.middleware import JWTAuthMiddlewareStack
import opportunities.routing
import notifications.routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(
                opportunities.routing.websocket_urlpatterns +
                notifications.routing.websocket_urlpatterns
            )
        )
    ),
})
```

`opportunities/routing.py`:
```python
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<username>[\w.@+-]+)/$', ChatConsumer.as_asgi()),
]
```

`notifications/routing.py`:
```python
websocket_urlpatterns = [
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
```

### 5.2 Room Naming Conventions

| Consumer | Room/Group Name | Example |
|----------|----------------|---------|
| ChatConsumer | `chat_{min_uid}_{max_uid}` | `chat_3_87` |
| NotificationConsumer | `notifications_{user_id}` | `notifications_42` |
| Presence | `presence_online` | (broadcast) |

Chat group key is always `chat_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}` to ensure the two users always resolve to the same group name regardless of who initiates.

### 5.3 Redis Channel Layer Configuration (Production)

```python
# settings/production.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL', default='redis://redis:6379/0')],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# settings/development.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
```

### 5.4 ChatConsumer — Detailed Design

`opportunities/consumers.py`:

```python
class ChatConsumer(AsyncWebsocketConsumer):
    """
    Handles real-time chat between two connected users.
    Group name: chat_{min_uid}_{max_uid}
    """

    async def connect(self):
        # 1. Authenticate via scope['user'] (set by JWTAuthMiddlewareStack)
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # 2. Resolve other user
        other_username = self.scope['url_route']['kwargs']['username']
        self.other_user = await get_user_or_close(other_username, self)

        # 3. Enforce connection requirement
        if not await is_connected(self.user, self.other_user):
            await self.close(code=4003)
            return

        # 4. Join group
        uids = sorted([self.user.id, self.other_user.id])
        self.room_group_name = f'chat_{uids[0]}_{uids[1]}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # 5. Mark user as online
        await cache.aset(f'online_{self.user.id}', True, timeout=300)
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'online.status',
            'user_id': self.user.id,
            'is_online': True,
        })
        await self.accept()

    async def disconnect(self, close_code):
        await cache.adelete(f'online_{self.user.id}')
        await cache.aset(f'last_seen_{self.user.id}', timezone.now().isoformat(), timeout=86400)
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'online.status',
            'user_id': self.user.id,
            'is_online': False,
            'last_seen': timezone.now().isoformat(),
        })
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')

        handlers = {
            'chat.message': self.handle_chat_message,
            'chat.typing': self.handle_typing,
            'chat.read_receipt': self.handle_read_receipt,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(data)

    async def handle_chat_message(self, data):
        content = data.get('content', '').strip()
        if not content:
            return
        msg = await save_message(self.user, self.other_user, content)
        payload = {
            'type': 'chat.message',
            'id': msg.id,
            'sender_id': self.user.id,
            'content': content,
            'timestamp': msg.timestamp.isoformat(),
            'is_delivered': False,
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    async def handle_typing(self, data):
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat.typing',
            'user_id': self.user.id,
            'username': self.user.username,
            'is_typing': data.get('is_typing', False),
        })

    async def handle_read_receipt(self, data):
        msg_ids = data.get('message_ids', [])
        await mark_messages_read(msg_ids, self.user)
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat.read_receipt',
            'reader_id': self.user.id,
            'message_ids': msg_ids,
        })

    # Channel layer event handlers (called when group_send dispatches)
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
        # Mark as delivered if receiver is online
        if event['sender_id'] != self.user.id:
            await mark_delivered(event['id'])
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat.delivered',
                'message_id': event['id'],
            })

    async def chat_typing(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps(event))

    async def chat_read_receipt(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_delivered(self, event):
        await self.send(text_data=json.dumps(event))

    async def online_status(self, event):
        await self.send(text_data=json.dumps(event))
```

### 5.5 NotificationConsumer — Detailed Design

`notifications/consumers.py`:

```python
class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Personal notification channel per user.
    Group name: notifications_{user_id}
    """

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        self.group_name = f'notifications_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Send current unread count on connect
        count = await get_unread_count(self.user)
        await self.send(text_data=json.dumps({
            'type': 'notification.count_update',
            'unread_count': count,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_new(self, event):
        await self.send(text_data=json.dumps(event))

    async def notification_count_update(self, event):
        await self.send(text_data=json.dumps(event))
```

### 5.6 WebSocket Event Payloads (JSON Schemas)

#### Chat Events

```json
// chat.message (client → server)
{ "type": "chat.message", "content": "Hello!" }

// chat.message (server → client)
{
  "type": "chat.message",
  "id": 1042,
  "sender_id": 3,
  "content": "Hello!",
  "timestamp": "2025-01-15T10:30:00Z",
  "is_delivered": false
}

// chat.typing
{ "type": "chat.typing", "user_id": 3, "username": "alice", "is_typing": true }

// chat.read_receipt (client → server)
{ "type": "chat.read_receipt", "message_ids": [1040, 1041, 1042] }

// chat.read_receipt (server → client)
{ "type": "chat.read_receipt", "reader_id": 7, "message_ids": [1040, 1041, 1042] }

// chat.delivered
{ "type": "chat.delivered", "message_id": 1042 }

// online.status
{ "type": "online.status", "user_id": 7, "is_online": true, "last_seen": null }
{ "type": "online.status", "user_id": 7, "is_online": false, "last_seen": "2025-01-15T10:28:00Z" }
```

#### Notification Events

```json
// notification.new (server → client)
{
  "type": "notification.new",
  "id": 201,
  "verb": "solution_upvoted",
  "actor_username": "bob",
  "actor_avatar": "/media/profiles/bob.jpg",
  "target_url": "/problems/5/solutions/",
  "preview": "Bob upvoted your solution",
  "is_read": false,
  "created_at": "2025-01-15T10:30:00Z"
}

// notification.count_update (server → client)
{ "type": "notification.count_update", "unread_count": 3 }
```

### 5.7 Typing Indicator Debounce (Client-Side)

```javascript
// static/js/chat.js
let typingTimeout = null;
let isTyping = false;

chatInput.addEventListener('input', () => {
    if (!isTyping) {
        isTyping = true;
        socket.send(JSON.stringify({ type: 'chat.typing', is_typing: true }));
    }
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        isTyping = false;
        socket.send(JSON.stringify({ type: 'chat.typing', is_typing: false }));
    }, 3000);  // 3-second debounce
});
```

### 5.8 Online/Offline Presence Tracking

- On WebSocket `connect`: set Redis key `online_{user_id} = True` with 300s TTL, broadcast `online.status` event to chat group.
- On WebSocket `disconnect`: delete Redis key, set `last_seen_{user_id} = <iso_timestamp>` (24h TTL), broadcast offline status.
- Chat header reads `online_{user_id}` from Redis via a REST endpoint `GET /api/v1/profiles/<username>/online-status/` which returns `{"is_online": true}` or `{"is_online": false, "last_seen": "..."}`.
- The consumer sends a presence ping every 4 minutes to keep the Redis TTL alive.

### 5.9 JWTAuthMiddlewareStack

WebSocket connections authenticate via the same JWT token passed as a query param:

```
wss://devlink.example.com/ws/chat/bob/?token=<access_token>
```

`core/middleware.py`:

```python
class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = dict(parse_qsl(query_string))
        token = params.get('token')
        if token:
            try:
                validated = UntypedToken(token)
                user_id = validated['user_id']
                scope['user'] = await get_user(user_id)
            except (InvalidToken, TokenError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = scope.get('user', AnonymousUser())
        return await super().__call__(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
```

---

## Part 6: Frontend Design System & UI/UX

### 6.1 Tailwind → Bootstrap 5 Migration Plan

The existing `base.html` loads Tailwind via CDN. The migration removes Tailwind and replaces it with Bootstrap 5 + Bootstrap Icons via a compiled static bundle.

**Step-by-step migration:**

1. Remove `<script src="https://cdn.tailwindcss.com"></script>` from `base.html`.
2. Add Bootstrap 5 CSS + JS via CDN (initial) or compiled static bundle (final):
   ```html
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
   <link rel="stylesheet" href="{% static 'css/devlink.css' %}">
   <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" defer></script>
   ```
3. Replace all Tailwind utility classes in existing templates with Bootstrap equivalents:
   - `flex items-center gap-4` → `d-flex align-items-center gap-3`
   - `rounded-lg border border-gray-200 bg-white p-4 shadow-sm` → `card p-3`
   - `text-sm text-gray-500` → `small text-muted`
   - `hover:bg-gray-100` → Bootstrap hover utilities or custom CSS
4. Replace Tailwind color variables in `style.css` with Bootstrap CSS custom properties.
5. Convert the existing contribution graph colors from Tailwind-specific hex values to Bootstrap-aware variables.

**Files to update during migration:**
- `templates/base.html` — full rewrite
- `templates/navbar.html` — Bootstrap navbar component
- All template files in `accounts/`, `problems/`, `solutions/`, `opportunities/`

### 6.2 Bootstrap 5 Theme — DevLink Brand Colors

`static/css/devlink.css`:

```css
:root {
  --dl-primary: #6366f1;         /* Indigo */
  --dl-primary-hover: #4f46e5;
  --dl-secondary: #0ea5e9;       /* Sky blue */
  --dl-dark-bg: #0f172a;         /* Dark background */
  --dl-dark-card: #1e293b;       /* Dark card background */
  --dl-dark-border: #334155;     /* Dark border */
  --dl-text-muted-dark: #94a3b8;

  /* Override Bootstrap primary */
  --bs-primary: var(--dl-primary);
  --bs-primary-rgb: 99, 102, 241;
  --bs-link-color: var(--dl-primary);
  --bs-link-hover-color: var(--dl-primary-hover);
}

[data-bs-theme="dark"] {
  --bs-body-bg: var(--dl-dark-bg);
  --bs-body-color: #e2e8f0;
  --bs-card-bg: var(--dl-dark-card);
  --bs-border-color: var(--dl-dark-border);
  --bs-secondary-color: var(--dl-text-muted-dark);
}

/* DevLink-specific components */
.dl-badge-easy    { background: #dcfce7; color: #166534; }
.dl-badge-medium  { background: #fef9c3; color: #854d0e; }
.dl-badge-hard    { background: #fee2e2; color: #991b1b; }

[data-bs-theme="dark"] .dl-badge-easy    { background: #14532d; color: #86efac; }
[data-bs-theme="dark"] .dl-badge-medium  { background: #713f12; color: #fde68a; }
[data-bs-theme="dark"] .dl-badge-hard    { background: #7f1d1d; color: #fca5a5; }

.dl-vote-btn { border: none; background: none; color: #6b7280; transition: color .15s; }
.dl-vote-btn.active-upvote { color: #6366f1; }
.dl-vote-btn.active-downvote { color: #ef4444; }

.dl-contribution-cell {
  width: 12px; height: 12px; border-radius: 2px; display: inline-block;
}
```

### 6.3 Dark Mode Implementation

Dark mode uses the Bootstrap 5 `data-bs-theme` attribute on the `<html>` element and persists to `localStorage`.

**Theme toggle script** (inlined in `<head>` of `base.html` to prevent FOUC):

```html
<script>
  (function() {
    const saved = localStorage.getItem('dl-theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', saved);
  })();
</script>
```

**Toggle button** (in navbar):

```html
<button id="theme-toggle" class="btn btn-link nav-link px-2" aria-label="Toggle dark mode">
  <i class="bi bi-sun-fill" id="theme-icon-light"></i>
  <i class="bi bi-moon-fill d-none" id="theme-icon-dark"></i>
</button>
```

**Toggle logic** (`static/js/theme.js`):

```javascript
const toggle = document.getElementById('theme-toggle');
const html = document.documentElement;
const iconLight = document.getElementById('theme-icon-light');
const iconDark = document.getElementById('theme-icon-dark');

function applyTheme(theme) {
    html.setAttribute('data-bs-theme', theme);
    localStorage.setItem('dl-theme', theme);
    iconLight.classList.toggle('d-none', theme === 'dark');
    iconDark.classList.toggle('d-none', theme === 'light');
}

toggle.addEventListener('click', () => {
    applyTheme(html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark');
});
```

### 6.4 Base Template Structure

`templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}DevLink{% endblock %}</title>

  <!-- Anti-FOUC theme script -->
  <script>(function(){var t=localStorage.getItem('dl-theme')||'light';document.documentElement.setAttribute('data-bs-theme',t)})();</script>

  <!-- Styles -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css">
  <link rel="stylesheet" href="{% static 'css/devlink.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  {% include "_navbar.html" %}

  <div class="container-xl py-4">
    {% include "_toast_container.html" %}
    {% block content %}{% endblock %}
  </div>

  <!-- Scripts -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/toastify-js"></script>
  <script src="{% static 'js/theme.js' %}"></script>
  <script src="{% static 'js/toast.js' %}"></script>
  <script>AOS.init({ duration: 400, once: true });</script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

### 6.5 Reusable Template Components

#### `templates/_navbar.html`

Bootstrap 5 responsive navbar with:
- Brand: `DevLink` linking to home
- Nav links: Problems, Opportunities, Connections (authenticated only)
- Global search input (triggers autocomplete API, authenticated)
- Notification bell `<i class="bi bi-bell">` with unread badge `<span class="badge bg-danger" id="notif-count"></span>`
- Dark mode toggle button
- User avatar dropdown (profile link, dashboard, security, logout) or Login/Signup buttons for guests

#### `templates/_sidebar.html`

Dashboard sidebar navigation with links to: Dashboard, My Problems, My Solutions, My Applications, My Bookmarks, Connections, Messages, Reputation, Settings.

#### `templates/_card_problem.html`

```html
<!-- Usage: {% include "_card_problem.html" with problem=problem %} -->
<div class="card mb-3" data-aos="fade-up">
  <div class="card-body">
    <div class="d-flex justify-content-between align-items-start">
      <h5 class="card-title mb-1">
        <a href="{% url 'problem_detail' problem.id %}" class="text-decoration-none">{{ problem.title }}</a>
      </h5>
      <span class="badge dl-badge-{{ problem.difficulty }}">{{ problem.difficulty|capfirst }}</span>
    </div>
    <p class="card-text small text-muted mb-2">{{ problem.description|truncatewords:20 }}</p>
    <div class="d-flex flex-wrap gap-1 mb-2">
      {% for tag in problem.tags.all %}
        <span class="badge bg-secondary-subtle text-secondary-emphasis">{{ tag.name }}</span>
      {% endfor %}
    </div>
    <div class="d-flex align-items-center gap-3 small text-muted">
      <span><i class="bi bi-eye"></i> {{ problem.view_count }}</span>
      <span><i class="bi bi-chat-left-text"></i> {{ problem.solution_count }}</span>
      <span><i class="bi bi-person"></i>
        <a href="{% url 'accounts:profile' problem.user.username %}">{{ problem.user.username }}</a>
      </span>
      <span class="ms-auto">{{ problem.created_at|timesince }} ago</span>
    </div>
  </div>
</div>
```

#### `templates/_card_solution.html`

Card showing: author avatar + username, vote count with up/down buttons (AJAX), accepted badge (if accepted), excerpt of explanation (first 100 chars), code language badge, edit history indicator, bookmark button.

#### `templates/_card_opportunity.html`

Card showing: title, type badge (Job/Internship/Freelance/Open Source), required skills chips, creator, deadline (if set), application count, bookmark button.

#### `templates/_card_user.html`

Card showing: avatar, username, full name, experience level badge, top 3 skills, reputation score, mutual connections count, Follow/Unfollow toggle button, Connect button (if not connected).

#### `templates/_pagination.html`

```html
{% if page_obj.has_other_pages %}
<nav aria-label="Page navigation">
  <ul class="pagination justify-content-center">
    {% if page_obj.has_previous %}
      <li class="page-item">
        <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
          <i class="bi bi-chevron-left"></i>
        </a>
      </li>
    {% endif %}
    {% for num in page_obj.paginator.page_range %}
      <li class="page-item {% if page_obj.number == num %}active{% endif %}">
        <a class="page-link" href="?page={{ num }}">{{ num }}</a>
      </li>
    {% endfor %}
    {% if page_obj.has_next %}
      <li class="page-item">
        <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
          <i class="bi bi-chevron-right"></i>
        </a>
      </li>
    {% endif %}
  </ul>
</nav>
{% endif %}
```

#### `templates/_empty_state.html`

```html
<!-- Usage: {% include "_empty_state.html" with icon="bi-inbox" title="No problems yet" cta_url=url cta_label="Post a Problem" %} -->
<div class="text-center py-5">
  <i class="bi {{ icon }} fs-1 text-muted d-block mb-3"></i>
  <h5 class="text-muted">{{ title }}</h5>
  {% if cta_url %}
    <a href="{{ cta_url }}" class="btn btn-primary mt-2">{{ cta_label }}</a>
  {% endif %}
</div>
```

#### `templates/_skeleton_card.html`

```html
<div class="card mb-3 placeholder-glow">
  <div class="card-body">
    <h5 class="card-title placeholder col-7"></h5>
    <p class="placeholder col-12"></p>
    <p class="placeholder col-9"></p>
    <div class="d-flex gap-2">
      <span class="placeholder col-2 badge"></span>
      <span class="placeholder col-2 badge"></span>
    </div>
  </div>
</div>
```

#### `templates/_toast_container.html`

```html
<div id="toast-container" class="position-fixed bottom-0 end-0 p-3" style="z-index: 1100"></div>
```

### 6.6 Page-Level Template Map

| URL Pattern | Template Path | Notes |
|-------------|--------------|-------|
| `/` | `templates/home.html` | Landing page, AOS animations |
| `/dashboard/` | `templates/dashboard.html` | Stats, chart, graph, quick actions |
| `/accounts/login/` | `accounts/templates/login.html` | |
| `/accounts/signup/` | `accounts/templates/signup.html` | |
| `/accounts/activate/<uid>/<token>/` | `accounts/templates/activation_result.html` | |
| `/accounts/forgot-password/` | `accounts/templates/forgot_password.html` | |
| `/accounts/reset-password/<uid>/<token>/` | `accounts/templates/password_reset_confirm.html` | |
| `/accounts/security/` | `accounts/templates/security.html` | Login history |
| `/profile/<username>/` | `accounts/templates/profile.html` | |
| `/profile/<username>/edit/` | `accounts/templates/edit_profile.html` | |
| `/problems/` | `problems/templates/problem_list.html` | Filters, search |
| `/problems/create/` | `problems/templates/problem_create.html` | EasyMDE |
| `/problems/<id>/` | `problems/templates/problem_detail.html` | Prism, solutions |
| `/problems/<id>/edit/` | `problems/templates/problem_edit.html` | |
| `/solutions/<id>/edit/` | `solutions/templates/solution_edit.html` | Monaco + EasyMDE |
| `/opportunities/` | `opportunities/templates/opportunity_list.html` | |
| `/opportunities/create/` | `opportunities/templates/opportunity_create.html` | |
| `/opportunities/<id>/` | `opportunities/templates/opportunity_detail.html` | |
| `/opportunities/<id>/edit/` | `opportunities/templates/opportunity_edit.html` | |
| `/applications/` | `opportunities/templates/application_list.html` | My applications |
| `/applications/manage/` | `opportunities/templates/applications.html` | Manage received |
| `/invitations/` | `opportunities/templates/invitation_list.html` | |
| `/invitations/sent/` | `opportunities/templates/sent_invitations.html` | |
| `/messages/` | `templates/messages_list.html` | Chat partner list |
| `/messages/<username>/` | `opportunities/templates/chat.html` | Real-time chat |
| `/notifications/` | `notifications/templates/notification_list.html` | |
| `/bookmarks/` | `bookmarks/templates/bookmark_list.html` | |
| `/search/` | `search/templates/search_results.html` | |
| `/reputation/` | `reputation/templates/reputation.html` | Score + badges + history |
| `404` | `templates/404.html` | |
| `500` | `templates/500.html` | |

### 6.7 JavaScript Libraries Integration

#### Toastify.js Helper (`static/js/toast.js`)

```javascript
window.showToast = function(message, type = 'success') {
    const colors = {
        success: 'linear-gradient(to right, #6366f1, #0ea5e9)',
        error: 'linear-gradient(to right, #ef4444, #dc2626)',
        warning: 'linear-gradient(to right, #f59e0b, #d97706)',
    };
    Toastify({
        text: message,
        duration: 4000,
        gravity: 'bottom',
        position: 'right',
        style: { background: colors[type] || colors.success },
        stopOnFocus: true,
    }).showToast();
};
```

Called throughout views and AJAX handlers: `showToast('Solution submitted!', 'success')`.

#### EasyMDE Configuration

Used in problem create/edit and solution create/edit for the `description`/`explanation` fields:

```javascript
const easyMDE = new EasyMDE({
    element: document.getElementById('id_description'),
    spellChecker: false,
    autosave: { enabled: true, uniqueId: 'problem-draft', delay: 3000 },
    toolbar: ['bold','italic','heading','|','quote','code','unordered-list','ordered-list',
              '|','link','image','|','preview','side-by-side','fullscreen','|','guide'],
    minHeight: '200px',
    previewClass: ['editor-preview', 'prose'],
});
```

#### Monaco Editor Configuration

Used for the `code` field in solution create/edit:

```javascript
require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.47.0/min/vs' }});
require(['vs/editor/editor.main'], function() {
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const editor = monaco.editor.create(document.getElementById('monaco-container'), {
        value: document.getElementById('id_code').value,
        language: 'python',
        theme: isDark ? 'vs-dark' : 'vs',
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        scrollBeyondLastLine: false,
    });
    // Sync Monaco content back to hidden textarea on form submit
    document.querySelector('form').addEventListener('submit', () => {
        document.getElementById('id_code').value = editor.getValue();
    });
    // Respond to dark mode toggle
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const nowDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        monaco.editor.setTheme(nowDark ? 'vs-dark' : 'vs');
    });
});
```

Language is auto-detected from a `<select id="id_language">` field; on change: `monaco.editor.setModelLanguage(editor.getModel(), selectedLang)`.

#### Prism.js Integration

Loaded on all pages that render Markdown HTML (problem detail, solution list):

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" id="prism-theme">
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-core.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    Prism.highlightAll();
    // Switch Prism theme for light/dark
    const updatePrismTheme = () => {
        const dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        document.getElementById('prism-theme').href = dark
            ? 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css'
            : 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css';
    };
    updatePrismTheme();
    document.getElementById('theme-toggle').addEventListener('click', updatePrismTheme);
});
</script>
```

#### AOS Usage

Cards in `home.html`, `problem_list.html`, `opportunity_list.html`:

```html
<div class="card mb-3" data-aos="fade-up" data-aos-delay="100">
```

AOS initialized in `base.html`: `AOS.init({ duration: 400, once: true, offset: 50 })`.

#### Contribution Graph

The existing vanilla JS contribution graph is kept as-is but updated to use Bootstrap CSS variables instead of hardcoded Tailwind colors:

```javascript
const colorFor = (count) => {
    const dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    if (count <= 0) return dark ? '#1e293b' : '#ebedf0';
    if (count === 1) return dark ? '#1d4ed8' : '#9be9a8';
    if (count === 2) return dark ? '#2563eb' : '#40c463';
    if (count <= 4) return dark ? '#3b82f6' : '#30a14e';
    return dark ? '#60a5fa' : '#216e39';
};
```

---

## Part 7: Deployment Architecture

### 7.1 Docker Compose Services

`docker-compose.yml`:

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      target: production
    restart: unless-stopped
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: Connect.settings.production
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    expose:
      - "8000"
    entrypoint: ["/app/docker/entrypoint.sh"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  daphne:
    build:
      context: .
      target: production
    restart: unless-stopped
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: Connect.settings.production
    command: daphne -b 0.0.0.0 -p 8001 Connect.asgi:application
    depends_on:
      - web
      - redis
    expose:
      - "8001"

  celery_worker:
    build:
      context: .
      target: production
    restart: unless-stopped
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: Connect.settings.production
    command: celery -A Connect worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - web

  celery_beat:
    build:
      context: .
      target: production
    restart: unless-stopped
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: Connect.settings.production
    command: celery -A Connect beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - redis
      - web

  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      - ./docker/certbot/conf:/etc/letsencrypt:ro
    depends_on:
      - web
      - daphne

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### 7.2 Dockerfile (Multi-Stage)

`Dockerfile`:

```dockerfile
# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libmagic1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt .
RUN pip install --no-cache-dir --prefix=/install -r production.txt

# ── Stage 2: Production ───────────────────────────────────────────
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libmagic1 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN addgroup --system devlink && adduser --system --group devlink && \
    chown -R devlink:devlink /app

USER devlink

EXPOSE 8000 8001
```

### 7.3 Docker Entrypoint Script

`docker/entrypoint.sh`:

```bash
#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn..."
exec gunicorn Connect.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --worker-class sync \
    --timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
```

### 7.4 Nginx Configuration

`docker/nginx.conf`:

```nginx
events { worker_connections 1024; }

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 20M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    upstream web {
        server web:8000;
    }

    upstream daphne {
        server daphne:8001;
    }

    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name devlink.example.com;

        ssl_certificate /etc/letsencrypt/live/devlink.example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/devlink.example.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Frame-Options DENY always;

        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /app/media/;
            expires 7d;
        }

        # WebSocket connections → Daphne
        location /ws/ {
            proxy_pass http://daphne;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 86400;
        }

        # HTTP → Gunicorn
        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 7.5 Settings Split

```
Connect/settings/
├── __init__.py
├── base.py          # Shared settings (INSTALLED_APPS, MIDDLEWARE, TEMPLATES, etc.)
├── development.py   # DEBUG=True, SQLite, InMemoryChannelLayer, EMAIL_BACKEND=console
└── production.py    # DEBUG=False, PostgreSQL, Redis, secure cookies, HTTPS
```

Selected via `DJANGO_SETTINGS_MODULE` environment variable:
- Local development: `Connect.settings.development`
- Docker production: `Connect.settings.production`

`settings/base.py` uses `django-environ`:

```python
import environ
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
```

### 7.6 Environment Variables (`.env.example`)

```bash
# Django
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=Connect.settings.production
ALLOWED_HOSTS=devlink.example.com,www.devlink.example.com
DEBUG=False

# Database (production)
DATABASE_URL=postgres://devlink:password@postgres:5432/devlink_db

# Redis
REDIS_URL=redis://redis:6379/0

# Email (SMTP)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@devlink.example.com

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Media storage (optional, for S3)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Postgres (used by docker-compose)
POSTGRES_DB=devlink_db
POSTGRES_USER=devlink
POSTGRES_PASSWORD=your-db-password
```

### 7.7 Health Check Endpoint

`core/views.py`:

```python
def health_check(request):
    """Returns 200 if the application is running. Used by Docker healthcheck."""
    return JsonResponse({'status': 'ok', 'service': 'devlink'})
```

URL: `path('api/health/', health_check, name='health_check')`

### 7.8 Celery Configuration

`Connect/celery.py`:

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Connect.settings.development')

app = Celery('Connect')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
from celery.schedules import crontab
app.conf.beat_schedule = {
    'delete-old-notifications': {
        'task': 'notifications.tasks.delete_old_notifications',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    'aggregate-daily-stats': {
        'task': 'core.tasks.aggregate_daily_stats',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

Task retry policy in `settings/base.py`:

```python
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_MAX_RETRIES = 3
# Exponential backoff: 60s, 300s, 900s
```

---

## Part 8: Development Roadmap (Phased Implementation Plan)

### Overview

Each phase is designed to be independently deployable without breaking existing functionality. Phases build on each other in dependency order.

---

### Phase 1 — Foundation & Infrastructure (Week 1)

**Goal:** Establish the infrastructure scaffold that all future phases depend on.

**Tasks:**
- Create `Connect/settings/` directory and split current `settings.py` into `base.py`, `development.py`, `production.py`
- Update `manage.py` and `asgi.py`/`wsgi.py` to use `DJANGO_SETTINGS_MODULE`
- Install `django-environ` and update settings to read from `.env`
- Add `DATABASE_URL` support in `production.py` (keep SQLite in `development.py`)
- Add Redis channel layer config in `production.py` (keep InMemoryChannelLayer in `development.py`)
- Migrate `base.html` from Tailwind CDN to Bootstrap 5 + Bootstrap Icons
- Create `static/css/devlink.css` with brand color variables and dark mode CSS
- Implement dark mode toggle (`static/js/theme.js`) with localStorage persistence
- Add AOS, Toastify.js, Bootstrap JS to `base.html`
- Create `static/js/toast.js` with `showToast()` helper
- Fix URL name conflict: rename `application_list` in `opportunities/urls.py` to `my_applications` (currently conflicts with URL name used in navbar)
- Install DRF, SimpleJWT, drf-spectacular: add to `requirements/base.txt` and `INSTALLED_APPS`
- Create `core` app with empty `services.py`, `selectors.py`, `permissions.py`, `validators.py`, `middleware.py`
- Add `core` to `INSTALLED_APPS`
- Create `api` app with DRF router skeleton and drf-spectacular schema view
- Wire up `/api/docs/` and `/api/redoc/` URLs
- Write `docker/entrypoint.sh`
- Create `requirements/base.txt`, `requirements/development.txt`, `requirements/production.txt`

**Verification:** All existing pages render correctly under Bootstrap 5. Dark mode toggle works. `/api/docs/` loads Swagger UI.

---

### Phase 2 — Auth Hardening (Week 2)

**Goal:** Harden authentication with email verification, JWT, login history, and rate limiting.

**Tasks:**
- Create `EmailOrUsernameBackend` in `accounts/backends.py`; add to `AUTHENTICATION_BACKENDS`
- Implement `Remember Me` — extend session lifetime in login view
- Create `LoginEvent` model and migration
- Record `LoginEvent` on every successful login in `accounts/views.py` login view
- Create Celery task `accounts/tasks.py`: `send_activation_email(user_id)`
- Modify `SignupView` to create `is_active=False` user and dispatch Celery task
- Implement `ActivateAccountView` at `/accounts/activate/<uidb64>/<token>/`
- Create `activation_result.html` and `activation_expired.html` templates
- Implement "Resend Activation" view
- Create Celery task `accounts/tasks.py`: `send_password_reset_email(email)`
- Implement `ForgotPasswordView` and `PasswordResetConfirmView`
- Add JWT token endpoints (`/api/auth/token/`, `/api/auth/token/refresh/`) via SimpleJWT
- Implement `RateLimitMiddleware` in `core/middleware.py` using Redis
- Add `SecurityHeadersMiddleware` to MIDDLEWARE list
- Create `AuditLog` model in `core/models.py` and migration
- Write `AuditService.log_event()` in `core/services.py`
- Integrate `AuditService` into login, logout, password reset views
- Create `security.html` template for login history page
- Implement `/accounts/security/` view showing 20 most recent `LoginEvent` records
- Implement session revoke action
- Write tests for auth flows in `accounts/tests.py`

**Verification:** Registration sends activation email (check Celery log). JWT token endpoint returns tokens. Login with email works. Rate limiting blocks after 5 failures.

---

### Phase 3 — Profile Extension (Week 3)

**Goal:** Enrich profiles with the full set of professional fields, follow system, and profile API.

**Tasks:**
- Add new fields to `Profile` model: `full_name`, `cover_photo`, `location`, `experience_level`, `languages`, `tech_stack`, `portfolio`, `resume`, `availability_status`, `about`, `reputation_score`; create and run migration
- Update `edit_profile.html` form to include all new fields with Bootstrap form layout
- Update `accounts/views.py` `EditProfileView` to handle file uploads (validate via `FileValidator`)
- Implement profile completion percentage calculation in `accounts/selectors.py`
- Update `profile.html` to display all new fields, cover photo, completion bar, follow stats
- Create `Follow` model and migration
- Implement `follow_user` and `unfollow_user` services in `accounts/services.py`
- Add follow/unfollow AJAX views and wire up toggle button in `_card_user.html` and profile page
- Create `ProfileReadSerializer` and `ProfileUpdateSerializer` in `accounts/serializers.py`
- Register `ProfileViewSet` (read-only list + detail + follow action) in `api` router
- Add `/api/v1/profiles/<username>/` endpoint
- Update contribution graph color scheme for dark mode compatibility
- Write profile tests in `accounts/tests.py`

**Verification:** Profile edit form saves all fields. Follow button toggles without page reload. `/api/v1/profiles/username/` returns JSON.

---

### Phase 4 — Problems & Solutions Enhancement (Week 4)

**Goal:** Add missing problem/solution features and downvote support.

**Tasks:**
- Add `category`, `view_count`, `is_deleted`, `updated_at` to `Problem` model; migrate
- Implement `ProblemView` model and migration
- Implement `record_problem_view(problem, request)` in `problems/services.py` using `F()` expression
- Add problem edit view at `/problems/<id>/edit/` with `IsOwner` check
- Add problem soft-delete view with cascade (mark all solutions/comments in memory, then soft-delete problem)
- Update `problem_list.html` to add category filter chips and updated sort controls
- Update `problem_detail.html` to show view count, category, edit/delete buttons (owner only)
- Add `ProblemAttachment` model and migration; allow up to 5 attachments on create/edit
- Add `vote_type` field to `Vote` model; create and run migration (default existing votes to 'upvote')
- Update `VoteService.cast_vote(user, solution, vote_type)` to handle upvote/downvote logic atomically
- Update vote AJAX endpoint and solution card vote buttons
- Add `SolutionEditHistory` model and migration
- Implement `edit_solution` service: save history record, update solution
- Add solution edit view at `/solutions/<id>/edit/`
- Add solution delete view
- Integrate reputation awards for problem creation (`+5`) and solution accept (`+25`) — wire via signals
- Write problem and solution tests

**Verification:** Problem view count increments once per user session. Downvote button works. Edit history logged. Reputation score updates on accept.

---

### Phase 5 — Comments, Reactions, Bookmarks (Week 5)

**Goal:** Add comment editing, reactions, pinning, and the full bookmark system.

**Tasks:**
- Add `is_pinned`, `is_edited`, `edited_at` to `Comment` model; migrate
- Implement comment edit AJAX view (returns updated comment HTML fragment or JSON)
- Implement comment delete AJAX view (cascades to replies)
- Add "edited" label rendering in `comment.html` template
- Create `CommentReaction` model and migration
- Implement `toggle_reaction(user, comment, reaction_type)` service
- Add reaction AJAX endpoint; render reaction bar in comment template
- Implement pin/unpin comment service and AJAX endpoint (problem author only)
- Create `Bookmark` app (`bookmarks`), `Bookmark` model, migration, `INSTALLED_APPS` addition
- Implement `bookmark_item(user, obj)` and `unbookmark_item(user, obj)` in `bookmarks/services.py`
- Add bookmark toggle AJAX endpoints for Problem, Solution, Opportunity
- Update problem_detail, solution list, and opportunity_detail templates with bookmark button
- Create `bookmark_list.html` — grouped by type (Problems, Solutions, Opportunities)
- Implement `/bookmarks/` view
- Implement `BookmarkSerializer` and `/api/v1/bookmarks/` endpoint
- Write bookmark and comment tests

**Verification:** React emojis toggle on comments. Bookmark button toggles without page reload. Bookmark list groups correctly.

---

### Phase 6 — Notifications (Week 6)

**Goal:** Deliver real-time notifications via WebSocket for all key events.

**Tasks:**
- Create `notifications` app; add to `INSTALLED_APPS`
- Create `Notification` model and migration
- Implement `NotificationConsumer` in `notifications/consumers.py`
- Add WebSocket URL `ws/notifications/` to routing
- Implement `NotificationService.create_notification(recipient, actor, verb, target)` in `notifications/services.py`; dispatches to channel layer via `async_to_sync`
- Wire notification creation to Django signals in `notifications/signals.py`:
  - `post_save` on `Invitation` (pending status → connection_request)
  - `post_save` on `Invitation` (accepted status → connection_accepted)
  - `post_save` on `Comment` → solution_commented (notify problem author)
  - `post_save` on `Solution` with `is_accepted=True` → solution_accepted
  - `post_save` on `Vote` → solution_upvoted / solution_downvoted
  - `post_save` on `Application` status change → application_accepted / application_rejected
- Add `notifications` to `apps.py` `ready()` to load signals
- Update `_navbar.html` to show unread count badge; connect `NotificationConsumer` via JS
- Create `notification_list.html` — sorted, read/unread styles, mark-all-read button
- Implement mark-as-read AJAX endpoint and mark-all-read endpoint
- Implement `NotificationSerializer` and `/api/v1/notifications/` API endpoint
- Create Celery Beat task: `delete_old_notifications` — delete `Notification` records older than 90 days
- Write notification tests

**Verification:** Cast a vote → notification appears in bell within 1 second. Mark all read → badge drops to 0.

---

### Phase 7 — Reputation & Badges (Week 7)

**Goal:** Build the full reputation and badge system.

**Tasks:**
- Create `reputation` app; add to `INSTALLED_APPS`
- Create `ReputationEvent`, `Badge`, `UserBadge` models and migration
- Seed `Badge` records via a data migration (5 badges defined in Req 16.5)
- Implement `ReputationService.award(user, event_type)` in `reputation/services.py`:
  - Use `transaction.atomic()` + `select_for_update()` on `Profile` to prevent race conditions
  - Create `ReputationEvent` record
  - Update `Profile.reputation_score` atomically
  - Trigger badge check
- Implement `ReputationService.compute_level(score)` returning level string
- Implement `BadgeService.check_and_award_badges(user)` — check all trigger conditions
- Wire `ReputationService.award()` calls via signals in `reputation/signals.py`:
  - Vote upvote/downvote/toggle (from `solutions` signals)
  - Solution accepted (from `solutions` signals)
  - Problem posted (from `problems` signals)
  - Comment posted (from `solutions` signals)
  - Connection established (from `opportunities` signals)
- Update `profile.html` to display reputation score, level, and badges with Bootstrap Icons
- Update dashboard to display reputation score and level
- Create `reputation.html` page with Chart.js reputation history chart
- Implement `ReputationEventSerializer` and `/api/v1/reputation/history/` endpoint
- Write reputation tests including atomic update tests

**Verification:** Upvoting adds +10 to author's score. Reaching 500 triggers Expert level. Badge awarded on first solution.

---

### Phase 8 — Chat Enhancement (Week 8)

**Goal:** Extend the existing chat with typing indicators, delivered/read receipts, file sharing, pagination, and pinned messages.

**Tasks:**
- Add `file_url`, `file_type`, `is_delivered`, `is_pinned` to `Message` model; migrate
- Rewrite `ChatConsumer` to implement: typing indicators (broadcast to group, debounce on client), delivered receipts (mark on receive), read receipts (mark on load), online/offline presence
- Implement `JWTAuthMiddlewareStack` in `core/middleware.py`
- Update `Connect/asgi.py` to use `JWTAuthMiddlewareStack`
- Implement `ChatFile` model and migration
- Add file upload endpoint `POST /messages/upload/` for chat files (validate MIME, size)
- Update `chat.html` frontend JS to handle all new event types
- Implement typing indicator UI: "alice is typing..." label with 3s auto-hide
- Implement message pagination: load last 50 on connect, `GET /messages/<username>/?before=<msg_id>` loads next 50
- Create `PinnedMessage` model and migration; implement pin/unpin endpoint
- Add pinned message panel at top of chat template
- Implement emoji picker (use `https://cdn.jsdelivr.net/npm/emoji-picker-element@1.21.3`)
- Write chat consumer tests using `WebsocketCommunicator`

**Verification:** Typing indicator appears and disappears after 3s. Scrolling to top loads older messages. File upload sends image preview.

---

### Phase 9 — Opportunities & Applications Enhancement (Week 9)

**Goal:** Add opportunity types, deadlines, application file uploads, and withdrawal.

**Tasks:**
- Add `opportunity_type`, `deadline`, `updated_at` to `Opportunity` model; migrate
- Update `opportunity_create.html` and `opportunity_edit.html` forms with type selector and deadline date picker
- Update `opportunity_list.html` with type filter buttons (Bootstrap button group)
- Update `opportunity_detail.html` to show type badge, deadline countdown, applicant count
- Add opportunity edit view at `/opportunities/<id>/edit/`
- Add opportunity soft-delete (set `is_active=False`) view
- Add `resume_file`, `portfolio` to `Application` model; migrate (keep `resume_url` for backward compat)
- Update application form to accept file upload OR URL (conditional UI via JS)
- Implement application withdraw action at `DELETE /api/v1/applications/<id>/`
- Update `application_list.html` to show withdraw button on pending applications
- Implement `OpportunityReadSerializer`, `OpportunityWriteSerializer`, `ApplicationSerializer`
- Register `OpportunityViewSet` and `ApplicationViewSet` in API router
- Write opportunity and application tests

**Verification:** Opportunity type badge renders. PDF resume uploads. Application withdrawal removes record.

---

### Phase 10 — Global Search & Admin (Week 10)

**Goal:** Implement global search and enhance the Django admin.

**Tasks:**
- Create `search` app; add to `INSTALLED_APPS`
- Implement `SearchService.search(query, search_type=None, ordering='relevance')` in `search/services.py`:
  - Uses `Q` objects: `Problem.objects.filter(Q(title__icontains=q) | Q(description__icontains=q))`
  - Combines results from: Users (via Profile), Problems, Solutions, Opportunities
  - Returns dict keyed by category with paginated QuerySet slices
- Implement autocomplete selector: returns top 3 per category, filtered to 2+ character queries
- Create `search_results.html` with category tab filters and result cards (using existing card partials)
- Implement autocomplete API endpoint `GET /api/v1/search/autocomplete/?q=<query>` returning JSON grouped by type
- Wire up global search input in navbar with debounced Fetch API autocomplete (300ms debounce)
- Create custom admin `AdminSite` subclass with analytics dashboard in `core/admin.py`
- Register all models in their respective `admin.py` files with proper `list_display`, `search_fields`, `list_filter`
- Implement admin analytics view showing: total users, problems, solutions, new registrations (7d), connections, messages
- Implement admin `AuditLog` view with date range filter and CSV export
- Implement admin User activate/deactivate action (logs to `AuditLog`)
- Write search tests

**Verification:** Typing "python" in search bar returns autocomplete within 300ms. Search results page shows results grouped by type.

---

### Phase 11 — REST API & Docs (Week 11)

**Goal:** Complete the full DRF API surface with all ViewSets, serializers, and documentation.

**Tasks:**
- Complete all ViewSets not yet implemented: `ProfileViewSet`, `ProblemViewSet`, `SolutionViewSet`, `CommentViewSet`, `VoteViewSet`, `OpportunityViewSet` (if not done), `ApplicationViewSet`, `ConnectionViewSet`, `InvitationViewSet`, `NotificationViewSet`, `BookmarkViewSet`, `SearchViewSet`, `ReputationViewSet`
- Register all ViewSets in `api/router.py`
- Add drf-spectacular `@extend_schema` decorators for all custom actions
- Configure `SPECTACULAR_SETTINGS` in `settings/base.py`
- Add custom `DevLinkPagination` class in `core/pagination.py`
- Add custom `custom_exception_handler` in `core/exceptions.py`; configure in `REST_FRAMEWORK` settings
- Implement `django-filter` filter classes for Problems, Solutions, Opportunities (`FilterSet`)
- Apply `RateLimitMiddleware` to all API routes
- Write API-level tests for all endpoints using DRF `APIClient`

**Verification:** `GET /api/docs/` renders full Swagger UI. All endpoints appear with correct schema. Rate limiting returns 429 after threshold.

---

### Phase 12 — Docker, CI, Final Polish (Week 12)

**Goal:** Production-ready Docker deployment, error pages, and final UI polish.

**Tasks:**
- Write `Dockerfile` (multi-stage builder/production)
- Write `docker-compose.yml` with all 6 services
- Write `docker/nginx.conf` with WebSocket proxying and HTTPS redirect
- Write `docker/entrypoint.sh`
- Create `requirements/production.txt` with all pinned versions
- Create `.env.example` documenting all environment variables
- Implement `404.html` and `500.html` error templates matching DevLink visual design; register custom error handlers in `Connect/urls.py`
- Add `_skeleton_card.html` and wire skeleton loaders to AJAX-loaded lists
- Audit all list pages for `data-aos="fade-up"` on card elements
- Final accessibility pass: add `aria-label` to all icon-only buttons, verify color contrast ratios, add `alt` text to all images
- Final responsive test: verify all pages at 320px, 768px, 1440px
- Run `manage.py check --deploy` and fix all warnings
- Write final integration tests for full flows: register → activate → login → post problem → submit solution → upvote → check reputation
- Update `README.md` with setup instructions for local dev and Docker deployment

**Verification:** `docker compose up` starts all 6 services. `https://localhost` serves the site with HTTPS. Existing tests still pass.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

The following properties are derived from the requirements acceptance criteria. Property-based testing applies here because the core business logic (voting, reputation, connections, bookmarks, Markdown parsing, pagination) involves pure functions and invariants that hold across all inputs — not just specific examples. The test library used is **Hypothesis** (Python) with a minimum of 100 iterations per property test.

---

### Property 1: Vote Count Net Invariant

*For any* Solution with an arbitrary sequence of upvote and downvote operations by distinct users, the Solution's computed net vote count SHALL always equal `(count of upvotes) - (count of downvotes)` across all Vote records for that Solution.

**Validates: Requirements 8.1, 8.2, 8.8**

---

### Property 2: Vote Toggle Round-Trip

*For any* authenticated User and any Solution they upvote and then toggle off, the Solution's net vote count SHALL return to its value before the upvote was cast — leaving no trace of the vote in the database.

**Validates: Requirements 8.3, 8.4**

---

### Property 3: Unique Vote Constraint

*For any* arbitrary sequence of vote and un-vote operations by User U on Solution S (including concurrent operations), at any point in time `Vote.objects.filter(user=U, solution=S).count()` SHALL be at most 1.

**Validates: Requirements 8.6**

*(Note: Properties 1, 2, and 3 consolidate requirements 8 voting properties — P1 and P7 from the original requirements are merged here since P7 is subsumed by Property 3.)*

---

### Property 4: Reputation Score Sum Invariant

*For any* User and any sequence of reputation-altering events applied to that User, `profile.reputation_score` SHALL always equal `sum(event.delta for event in user.reputation_events.all())`.

**Validates: Requirements 16.2, 16.7**

---

### Property 5: Reputation Event Idempotence

*For any* reputation-altering event, attempting to create a duplicate `ReputationEvent` record for the same event source (same user, same event type, same source object) SHALL NOT change the User's reputation score — the second call is a no-op.

**Validates: Requirements 16.7**

---

### Property 6: Connection Symmetry

*For any* two Users A and B, `is_connected(A, B)` SHALL always equal `is_connected(B, A)` — connection is bidirectional and symmetric at all times.

**Validates: Requirements 10.2, 10.5**

---

### Property 7: Connection Round-Trip

*For any* two Users A and B where A sends an Invitation, B accepts it, and A then removes the Connection, the resulting state SHALL be identical to the initial state: no Connection record exists and no pending Invitation exists between A and B.

**Validates: Requirements 10.2, 10.5**

---

### Property 8: Bookmark Idempotence

*For any* authenticated User U and any bookmarkable item I (Problem, Solution, or Opportunity), calling `bookmark_item(U, I)` twice SHALL result in exactly one `Bookmark` record — the second call is a no-op.

**Validates: Requirements 15.2**

---

### Property 9: Bookmark Removal Invariant

*For any* authenticated User U and any item I they have previously bookmarked, after calling `unbookmark_item(U, I)`, `Bookmark.objects.filter(user=U, content_type=ct, object_id=I.id).count()` SHALL equal 0.

**Validates: Requirements 15.4**

*(Note: Properties 8 and 9 are kept separate — idempotence of creation and the post-removal invariant are distinct correctness conditions.)*

---

### Property 10: Markdown Round-Trip Safety

*For any* valid Markdown string S submitted by a User, the rendered HTML output SHALL NOT contain `<script>`, `<style>`, or any `on*=` event-handler attributes.

**Validates: Requirements 25.2, 20.4**

---

### Property 11: Markdown Semantic Round-Trip

*For any* valid Markdown string S, `parse(render(parse(S)))` SHALL produce semantically equivalent content to `parse(S)` — no content is lost or corrupted through a parse → render → parse cycle.

**Validates: Requirements 25.4**

---

### Property 12: Pagination Completeness

*For any* paginated API list endpoint with N total items and page size P, iterating through all pages by following `next` links SHALL yield exactly N unique items in total, with no duplicates and no omissions.

**Validates: Requirements 18.3, 23.5**

---

### Property 13: Solution Accept Exclusivity

*For any* Problem P at any point in time, after any sequence of accept and unaccept operations, `Solution.objects.filter(problem=P, is_accepted=True).count()` SHALL be at most 1.

**Validates: Requirements 7.5**

---

### Property 14: Notification Timestamp Ordering

*For any* User who has received a sequence of N notifications, the Notification Center SHALL return all N notifications sorted by `created_at` descending — for any two notifications A and B where `A.created_at > B.created_at`, A SHALL appear before B in the results list.

**Validates: Requirements 12.3, 12.9**

---

### Property 15: JWT Token Round-Trip

*For any* valid User with a known `user_id`, the JWT access token issued during login, when decoded with the correct secret key before expiry, SHALL return the same `user_id` without modification.

**Validates: Requirements 2.2, 2.5**

---

## Error Handling

### Web UI Error Handling

- **400 Validation errors**: Form re-renders with inline Bootstrap `is-invalid` class on offending fields and a `invalid-feedback` div with the error message.
- **403 Permission denied**: Redirect to a custom `403.html` page or the login page (for unauthenticated users) without revealing whether the resource exists.
- **404 Not found**: Render `templates/404.html` with a link to the homepage.
- **500 Server error**: Render `templates/500.html`. Django's `DEBUG = False` ensures no stack trace is shown to users.
- **AJAX errors**: All AJAX handlers catch `response.ok` failures and call `showToast('Something went wrong. Please try again.', 'error')`.

### API Error Handling

All API errors use the standard error format via the custom exception handler in `core/exceptions.py`:

```json
{ "error": "...", "code": "...", "details": {} }
```

Specific error codes:

| Scenario | HTTP Status | Code |
|----------|-------------|------|
| Auth token expired | 401 | `token_expired` |
| Invalid credentials | 401 | `authentication_failed` |
| Permission denied | 403 | `permission_denied` |
| Resource not found | 404 | `not_found` |
| Validation failure | 400 | `validation_error` |
| Rate limit exceeded | 429 | `rate_limit_exceeded` |
| Duplicate resource | 409 | `duplicate_resource` |

### Celery Task Error Handling

All Celery tasks follow the retry pattern:

```python
@shared_task(bind=True, max_retries=3)
def send_activation_email(self, user_id):
    try:
        # ... task logic
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        # Delays: 60s, 120s, 240s
```

After 3 failed retries, the exception is logged to the application error log with task name, arguments, and full traceback.

### WebSocket Error Handling

- **Code 4001** — Unauthenticated connection: consumer closes immediately.
- **Code 4003** — Not connected to the chat partner: consumer closes with a message.
- **Malformed JSON**: Consumer catches `json.JSONDecodeError`, logs it, and continues without crashing.
- **Channel layer timeout**: Consumer catches `asyncio.TimeoutError` and attempts reconnection.

---

## Testing Strategy

### Dual Testing Approach

Two complementary testing strategies are used:

1. **Example-based unit tests** — `accounts/tests.py`, `problems/tests.py`, etc. using Django's `TestCase` and DRF's `APIClient`. Tests verify specific flows, integration points, edge cases, and error conditions.

2. **Property-based tests** — using **Hypothesis** library for the 15 correctness properties above. Each property test runs a minimum of 100 iterations with generated inputs.

### Unit Test Coverage Requirements

- Minimum **80% coverage** on all `services.py` and `selectors.py` files.
- All permission classes covered with tests for the positive (access granted) and negative (access denied) cases.
- All serializer `validate()` methods tested with valid and invalid inputs.
- All Celery tasks tested with mocked email/external calls.

### Property-Based Test Configuration (Hypothesis)

Install: `hypothesis[django]`

Settings (`conftest.py`):

```python
from hypothesis import settings, HealthCheck

settings.register_profile("ci", max_examples=200, suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("dev", max_examples=50)
settings.load_profile("ci" if os.environ.get('CI') else "dev")
```

Each property test is tagged with its design property number:

```python
@given(
    solutions=st.lists(st.builds(SolutionFactory), min_size=1, max_size=10),
    vote_sequences=st.lists(st.sampled_from(['upvote', 'downvote', None]), min_size=1)
)
@settings(max_examples=100)
# Feature: devlink-v1, Property 1: Vote Count Net Invariant
def test_vote_count_invariant(solutions, vote_sequences):
    ...
```

### Integration Tests

Integration tests cover the complete request-response cycle for critical paths:

- Register → activate email → login → post problem → submit solution → upvote → check reputation score
- Send invitation → accept → verify connection bidirectionality → send message via WebSocket
- Create opportunity → apply → accept application → verify notification delivered

WebSocket integration tests use Django Channels' `WebsocketCommunicator`:

```python
from channels.testing import WebsocketCommunicator

async def test_chat_message_delivered():
    communicator = WebsocketCommunicator(application, '/ws/chat/bob/?token=<token>')
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to({'type': 'chat.message', 'content': 'Hello'})
    response = await communicator.receive_json_from()
    assert response['type'] == 'chat.message'
    assert response['content'] == 'Hello'
    await communicator.disconnect()
```

### What is NOT Property-Based Tested

The following features use example-based tests only (PBT is not appropriate):

- File upload validation (MIME check, size limit) — example tests with specific file fixtures
- Email sending (Celery tasks) — mocked with `unittest.mock.patch`
- Django admin pages — example tests with admin client
- Template rendering — snapshot-style example tests
- WebSocket connection lifecycle — example tests with `WebsocketCommunicator`
- Docker health check endpoint — single smoke test
