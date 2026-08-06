# 🚀 DevLink Complete Project Masterclass & Architecture Guide

Welcome to the **Complete DevLink Engineering Masterclass**. This document is designed to teach you how to build, architect, and understand the entire **DevLink** application from absolute scratch.

---

## 🏛️ Part 1: High-Level Architecture & What DevLink Is

### What is DevLink?
**DevLink** is a full-stack social collaboration platform built for developers. It combines 5 core capabilities:
1. **Developer Portfolios & Profiles**: Showcasing tech stacks, Github links, avatars, and reputation scores.
2. **Community Problem Solving**: Asking technical coding questions with Markdown support and syntax highlighting.
3. **Open Solutions Repository**: Browsing, filtering, and upvoting community solutions.
4. **Developer Opportunity Marketplace**: Posting freelance projects, full-time jobs, and searching developers by tech stack (**Find Developers Modal**).
5. **Real-time Collaboration**: Direct messaging, connection requests, and real-time WebSocket notifications.

---

## 🔄 The Master Request-Response Lifecycle Diagram

Every single user request in DevLink follows this exact execution path through Django:

```
Developer Browser (HTTP GET/POST)
       │
       ▼
WSGI / ASGI Server (Gunicorn / Daphne)
       │
       ▼
Middleware Stack (Security, Session, Auth, SecurityHeaders)
       │
       ▼
URL Router (Connect/urls.py & App urls.py)
       │
       ▼
View Function / Class (views.py)
       │
       ▼
Database Model (models.py / Django ORM)
       │
       ▼
Database (SQLite in Dev / PostgreSQL in Prod)
       │
       ▼
View (Combines Data + Template Context)
       │
       ▼
Template Rendering Engine (base.html + HTML Template)
       │
       ▼
Browser Displays Rendered Page (HTML + CSS + JS)
```

---

## 📁 Directory Sitemap & How Every File Connects

Below is the directory sitemap of the DevLink codebase and the exact responsibility of each major file:

```
Connect/
│── manage.py                 <-- CLI entry point for running commands (migrate, runserver, createsuperuser)
│── Connect/                  <-- Project Root Configuration Package
│   ├── settings/
│   │   ├── base.py           <-- Core settings (INSTALLED_APPS, MIDDLEWARE, TEMPLATES)
│   │   ├── development.py    <-- Dev environment settings (DEBUG=True, SQLite)
│   │   └── production.py     <-- Production settings (WhiteNoise, PostgreSQL, Security)
│   ├── urls.py               <-- Master URL Router (includes app URLs)
│   ├── asgi.py               <-- Asynchronous Server Gateway Interface (WebSockets)
│   └── wsgi.py               <-- Web Server Gateway Interface (HTTP requests)
│
│── accounts/                 <-- MODULE 1: Users, Authentication & Profiles
│   ├── models.py             <-- Profile model (bio, profile_image, tech_stack, github_url)
│   ├── views.py              <-- signup_view, profile_view, edit_profile
│   ├── urls.py               <-- /accounts/login/, /accounts/signup/, /accounts/profile/
│   ├── signals.py            <-- Auto-creates Profile when User is registered
│   └── templates/            <-- login.html, signup.html, edit_profile.html
│
│── problems/                 <-- MODULE 2: Coding Problems & Questions
│   ├── models.py             <-- Problem model (title, description, tags, difficulty)
│   ├── views.py              <-- problem_list, create_problem, problem_detail
│   └── urls.py               <-- /problems/, /problems/create/, /problems/<id>/
│
│── solutions/                <-- MODULE 3: Solutions & Code Snippets
│   ├── models.py             <-- Solution model (problem FK, user FK, code, explanation, votes)
│   ├── views.py              <-- submit_solution, upvote_solution
│   └── urls.py               <-- /solutions/submit/, /solutions/<id>/upvote/
│
│── opportunities/            <-- MODULE 4: Opportunities, Jobs & Connections
│   ├── models.py             <-- Opportunity, Application, Connection, Invitation models
│   ├── views.py              <-- opportunity_list, find_developers, connection_list
│   └── urls.py               <-- /opportunities/, /opportunities/connections/
│
│── notifications/            <-- MODULE 5: Real-Time Notifications
│   ├── models.py             <-- Notification model (recipient, sender, verb, target, is_read)
│   ├── consumers.py          <-- WebSocket NotificationConsumer for instant alerts
│   ├── context_processors.py <-- Injects unread_notification_count into all templates
│   └── views.py              <-- /notifications/unread-count/ HTTP polling fallback
│
│── messages/                 <-- MODULE 6: Real-Time Direct Chat
│   ├── models.py             <-- Message & Conversation models
│   ├── consumers.py          <-- ChatConsumer for WebSocket 1-on-1 messaging
│   └── views.py              <-- message_list_view
│
│── dashboard/                <-- MODULE 7: Developer Analytics & Overview
│   └── views.py              <-- dashboard_view (aggregates problems, solutions, reputation)
│
│── reputation/               <-- MODULE 8: Gamification & Badges
│   ├── models.py             <-- ReputationPoint, Badge models
│   └── services.py           <-- award_points(), calculate_user_badges()
│
│── bookmarks/ & user_collections/ <-- MODULE 9 & 10: Saved Items & Lists
│
└── templates/                <-- Master Global HTML Templates
    ├── base.html             <-- Parent master layout (head, navbar, messages, scripts)
    └── components/
        └── navbar.html       <-- Fixed header navigation bar
```

---

## 🎓 Part 2: Module-by-Module Deep Dive

---

### 📘 MODULE 1: Accounts (`accounts`) - User Auth & Developer Profiles

#### 1. Purpose of Module
Manages identity, authentication, profile customization, Google OAuth sign-in, and developer attributes (avatar, bio, github link, tech stack).

#### 2. Database Models (`accounts/models.py`)

```python
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    # One-to-One relationship: Every User has exactly ONE Profile, and every Profile belongs to ONE User.
    # on_delete=models.CASCADE means if User is deleted, their Profile is deleted automatically.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    bio = models.TextField(max_length=500, blank=True, help_text="Short developer bio")
    profile_image = models.ImageField(upload_to='profile_images/', default='default.png', blank=True)
    location = models.CharField(max_length=100, blank=True)
    github_url = models.URLField(max_length=200, blank=True)
    website_url = models.URLField(max_length=200, blank=True)
    tech_stack = models.CharField(max_length=255, blank=True, help_text="Comma-separated tech keywords (e.g. Python, Django, React)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
```

#### 3. Automatic Signals (`accounts/signals.py`)
In Django, **Signals** allow decoupled applications to get notified when certain actions occur. We use `post_save` on the `User` model to automatically create a `Profile` whenever a new user registers:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
```

---

### 📘 MODULE 2: Problems (`problems`) - Questions & Discussion

#### 1. Database Model (`problems/models.py`)

```python
from django.db import models
from django.contrib.auth.models import User

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problems')
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Detailed problem description supporting Markdown")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    tags = models.CharField(max_length=255, help_text="Comma-separated tags e.g. python, django, dynamic-programming")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
```

---

### 📘 MODULE 3: Solutions (`solutions`) - Submissions & Voting

#### 1. Database Model (`solutions/models.py`)

```python
from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem

class Solution(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solutions')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solutions')
    code_content = models.TextField(help_text="Code submission")
    explanation = models.TextField(blank=True, help_text="Explanation of approach")
    upvotes = models.ManyToManyField(User, related_name='upvoted_solutions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_upvotes(self):
        return self.upvotes.count()

    def __str__(self):
        return f"Solution by {self.author.username} for {self.problem.title}"
```

---

### 📘 MODULE 4: Opportunities & Connections (`opportunities`)

#### 1. Connection & Invitation Models (`opportunities/models.py`)

```python
from django.db import models
from django.contrib.auth.models import User

class Connection(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_connections')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"
```

---

### 📘 MODULE 5: Real-Time Notifications (`notifications`)

#### 1. Notification Model (`notifications/models.py`)

```python
from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    verb = models.CharField(max_length=255)
    target_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

#### 2. Universal Context Processor (`notifications/context_processors.py`)
Injects `unread_notification_count` into every template context across the entire site automatically without cluttering individual views:

```python
def unread_notifications(request):
    if not request.user.is_authenticated:
        return {'unread_notification_count': 0}
    return {'unread_notification_count': request.user.notifications.filter(is_read=False).count()}
```

---

## ❓ Part 3: 10 Core Interview Questions & Exercises

1. **Q1: What is the difference between `select_related` and `prefetch_related` in Django ORM?**
   - *Answer*: `select_related` uses SQL `INNER JOIN` for single-valued relationships (`ForeignKey`, `OneToOneField`). `prefetch_related` uses separate SQL queries and performs joining in Python for multi-valued relationships (`ManyToManyField`, reverse `ForeignKey`).

2. **Q2: Why do we use `reverse_lazy` instead of `reverse` in `urls.py` or class-based views?**
   - *Answer*: `reverse` executes immediately when the file is parsed (before routes are registered). `reverse_lazy` evaluates lazily when the URL is actually accessed at runtime.

3. **Q3: What does `on_delete=models.CASCADE` vs `models.SET_NULL` do?**
   - *Answer*: `CASCADE` deletes child objects when the parent object is deleted. `SET_NULL` keeps child objects and sets the foreign key reference column to `NULL` (requires `null=True`).

4. **Q4: How does Django prevent Cross-Site Request Forgery (CSRF)?**
   - *Answer*: Uses a secret token stored in a user session cookie and embedded in HTML forms via `{% csrf_token %}`. `CsrfViewMiddleware` verifies that the submitted token matches the session cookie.

5. **Q5: Why did the login page error message fail to render initially?**
   - *Answer*: Django's `LoginView` places authentication errors into `form.non_field_errors`. Omitting `{% if form.non_field_errors %}` in templates suppresses error messages.

6. **Q6: Why did `/accounts/password_reset/` return a 500 error previously?**
   - *Answer*: The `accounts` app used URL namespacing (`app_name = 'accounts'`). Django's default password reset template attempted to reverse the unnamespaced route `'password_reset_confirm'`, throwing a `NoReverseMatch` exception.

7. **Q7: What causes a CSS Stacking Context issue that hides popups behind a navbar?**
   - *Answer*: Giving the navbar a higher `z-index` than popups/modals, or applying `transform`, `filter`, or `opacity < 1` to parent elements.

8. **Q8: How does Django's signals mechanism work?**
   - *Answer*: Event senders emit signals (e.g. `post_save`). Registered receivers listen for that signal and execute background callbacks automatically.

9. **Q9: How do WebSockets differ from HTTP requests in Django Channels?**
   - *Answer*: HTTP is stateless request-response over WSGI. WebSockets establish persistent, full-duplex continuous connections over ASGI for real-time bi-directional communication.

10. **Q10: What command validates Django configuration without starting the server?**
    - *Answer*: `python manage.py check`.

---

### 💻 Practical Exercises
1. **Exercise 1**: Create a custom template tag `tech_stack_badges` that splits `"Python, Django, React"` into HTML pill elements.
2. **Exercise 2**: Implement an AJAX view using `JsonResponse` to toggle bookmarks without refreshing the page.
3. **Exercise 3**: Write a `post_save` signal receiver that awards 15 reputation points to a user whenever they post a new solution.
