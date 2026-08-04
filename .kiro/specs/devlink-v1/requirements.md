# Requirements Document — DevLink v1.0

## Introduction

DevLink v1.0 is a production-ready developer networking platform built on top of the existing "Connect" Django project. The goal is to transform the current application — which already has accounts, problems, solutions, opportunities, invitations, connections, and real-time chat — into a polished, scalable, feature-rich platform for developers to network, collaborate, share knowledge, and discover opportunities.

**Core principle:** Do not rewrite from scratch. Preserve all existing functionality. Refactor incrementally. Add new features as modular Django apps following SOLID principles.

**Existing functionality to preserve:**
- User signup, login, logout, profile view, edit profile
- Problem CRUD with tags and difficulty
- Solution submission, voting (upvote), and accept solution
- Nested comments on solutions
- Opportunity listing, detail, create, and apply
- Application management (accept/reject)
- Invitation system (send/accept/reject)
- Connection creation on invitation acceptance
- Real-time WebSocket chat (Django Channels)
- Basic dashboard and contribution graph

---

## Glossary

- **DevLink**: The platform being built (the System).
- **System**: DevLink — the Django web application.
- **User**: An authenticated human interacting with DevLink.
- **Guest**: An unauthenticated visitor of DevLink.
- **Profile**: Extended user record storing biographical, social, and professional information.
- **Problem**: A technical challenge or question posted by a User for others to solve.
- **Solution**: A response to a Problem, containing explanation and/or code, submitted by a User.
- **Comment**: A text response attached to a Solution, supporting nested replies.
- **Vote**: A User's upvote or downvote cast on a Solution.
- **Opportunity**: A job, internship, freelance, or open-source posting created by a User.
- **Application**: A User's submission expressing interest in an Opportunity.
- **Invitation**: A connection request sent from one User to another.
- **Connection**: A bidirectional peer relationship between two Users, established when an Invitation is accepted.
- **Message**: A direct text (or file) communication sent from one User to another via real-time chat.
- **Notification**: A system-generated event alert delivered to a User in real-time.
- **Bookmark**: A User's saved reference to a Problem, Solution, or Opportunity.
- **Reputation**: A numeric score reflecting a User's contributions and community standing.
- **Badge**: A visual achievement awarded to a User based on milestones or reputation thresholds.
- **Tag**: A keyword label attached to Problems.
- **Category**: A broader classification for Problems beyond tags.
- **JWT**: JSON Web Token used for stateless API authentication via SimpleJWT.
- **Session**: Django's server-side session mechanism for web UI authentication.
- **API**: The Django REST Framework REST API exposed by DevLink.
- **WebSocket**: The persistent connection protocol used for real-time chat and notifications via Django Channels.
- **Celery**: The distributed task queue used for background processing (emails, notifications, stats).
- **Redis**: The in-memory data store used as the channel layer for WebSocket and as a Celery broker.
- **PostgreSQL**: The relational database used in production.
- **Docker**: The container runtime used for deployment.
- **Nginx**: The reverse proxy and static file server used in production.
- **Gunicorn**: The WSGI application server used in production.
- **EasyMDE**: The Markdown editor library used in problem and solution forms.
- **Monaco_Editor**: The code editor library used for solution code blocks.
- **Prism**: The syntax highlighting library used for rendering code.
- **Bootstrap_5**: The CSS framework used for the UI.
- **Toastify**: The JavaScript toast notification library.
- **AOS**: Animate On Scroll — the animation library used in the UI.
- **Chart.js**: The charting library used for dashboard statistics.
- **drf_spectacular**: The OpenAPI schema generation library for API documentation.
- **Rate_Limiter**: The middleware component enforcing request rate limits per User or IP.
- **Audit_Log**: A record of security-sensitive actions performed by Users.
- **RBAC**: Role-Based Access Control — the permission model used to restrict actions.
- **Validator**: A component that verifies input data meets defined constraints before processing.
- **Serializer**: A DRF component that converts model instances to/from JSON for the API.
- **Selector**: A service-layer function responsible only for querying data.
- **Service**: A service-layer function responsible for business logic and mutations.
- **Consumer**: A Django Channels WebSocket handler class.
- **Contribution_Graph**: A GitHub-style heatmap showing a User's activity over time.
- **Celery_Beat**: The periodic task scheduler component of Celery.

---

## Requirements

### Requirement 1: User Registration and Account Activation

**User Story:** As a Guest, I want to register for a DevLink account with email verification, so that I can confirm my identity and access the platform securely.

#### Acceptance Criteria

1. WHEN a Guest submits a valid registration form with a unique username, unique email, and a password meeting the strength policy, THE System SHALL create an inactive User account, send an activation email via Celery, and display a confirmation message instructing the Guest to verify their email.
2. IF a Guest submits a registration form with an email address that already exists in the System, THEN THE System SHALL return a validation error message identifying the duplicate field without creating any account.
3. IF a Guest submits a registration form with a username that already exists in the System, THEN THE System SHALL return a validation error message identifying the duplicate field without creating any account.
4. IF a Guest submits a password shorter than 8 characters or matching common password patterns, THEN THE System SHALL reject the registration and return a descriptive password-strength error.
5. WHEN a Guest clicks the activation link sent to their email within 24 hours, THE System SHALL activate the User account and redirect the User to the login page with a success message.
6. IF a Guest clicks an activation link that has expired (older than 24 hours), THEN THE System SHALL display an expiration error and offer a link to resend the activation email.
7. THE System SHALL hash all User passwords using Django's default PBKDF2 algorithm before storing them in the database.
8. FOR ALL registration attempts, the System SHALL validate inputs server-side regardless of any client-side validation present.

### Requirement 2: Authentication — Login, Logout, JWT, and Session

**User Story:** As a User, I want to log in using my username or email and password through both web UI and API, so that I can access my account across different clients.

#### Acceptance Criteria

1. WHEN a User submits a valid username-or-email and password combination via the web login form, THE System SHALL authenticate the User using Django session authentication and redirect them to their dashboard.
2. WHEN a User submits valid credentials to the `/api/auth/token/` endpoint, THE System SHALL return a JWT access token (lifetime: 60 minutes) and a refresh token (lifetime: 7 days).
3. WHEN a User submits a valid refresh token to the `/api/auth/token/refresh/` endpoint, THE System SHALL return a new access token without requiring re-entry of credentials.
4. IF a User submits an invalid username, email, or password via the login form, THEN THE System SHALL display a generic authentication failure message without indicating which field was incorrect.
5. IF a User submits an expired or invalid JWT to a protected API endpoint, THEN THE System SHALL return HTTP 401 with a descriptive error body.
6. WHEN a User logs out via the web UI, THE System SHALL invalidate the server-side session and redirect the User to the login page.
7. WHEN a User checks "Remember Me" on the login form, THE System SHALL extend the session cookie lifetime to 30 days.
8. THE System SHALL record each successful login event including timestamp and IP address in the Audit_Log.
9. IF a User makes 5 consecutive failed login attempts from the same IP address within 10 minutes, THEN THE System SHALL temporarily block that IP for 15 minutes and return an informative error.
10. THE System SHALL support login using either username or email address as the identifier field.

### Requirement 3: Password Reset and Recovery

**User Story:** As a User, I want to reset my password via email if I forget it, so that I can regain access to my account.

#### Acceptance Criteria

1. WHEN a User submits their email address on the forgot-password form, THE System SHALL send a password-reset email containing a time-limited token link via Celery, regardless of whether the email exists, to prevent email enumeration.
2. WHEN a User clicks a valid password-reset link and submits a new password that meets the strength policy, THE System SHALL update the User's password and invalidate the reset token.
3. IF a User clicks a password-reset link that has expired (older than 1 hour), THEN THE System SHALL display an expiration error and offer the forgot-password form again.
4. IF a User submits a new password that does not meet the strength policy on the reset form, THEN THE System SHALL reject the submission and return a descriptive validation error.
5. THE System SHALL invalidate all existing sessions for a User immediately after a successful password reset.

### Requirement 4: User Profile

**User Story:** As a User, I want a rich public profile page that showcases my skills, experience, contributions, and social links, so that other developers can learn about me and connect.

#### Acceptance Criteria

1. THE System SHALL display a User's public Profile page at `/profile/<username>/` containing: cover photo, profile image, username, full name, bio, about section, location, experience level, skills, tech stack, spoken languages, GitHub link, LinkedIn link, portfolio website link, availability status, reputation score, badges, follower count, following count, connections count, and join date.
2. WHEN a User views their own Profile page, THE System SHALL display an "Edit Profile" button that navigates to the profile editing form.
3. WHEN a User submits a valid profile edit form, THE System SHALL save the changes and redirect back to the updated Profile page within 2 seconds.
4. THE System SHALL display a profile completion percentage calculated as the ratio of filled optional profile fields to total optional profile fields, updated in real-time during editing.
5. WHEN a User uploads a profile image or cover photo, THE System SHALL validate that the file is an image (JPEG, PNG, or WebP), has a maximum size of 5 MB, and store it in the configured media storage backend.
6. IF a User uploads a file that is not an accepted image format or exceeds 5 MB, THEN THE System SHALL reject the upload and return a descriptive validation error without saving any changes.
7. THE System SHALL render the Contribution_Graph on each public Profile page, showing the User's daily activity count (problems posted + solutions submitted) for the selected year.
8. WHEN a Guest views a User's public Profile, THE System SHALL display all public information but hide edit controls and action buttons.
9. THE System SHALL display the User's top skills derived from the tags of problems they have solved, ordered by frequency descending.
10. THE System SHALL expose profile data via a read-only API endpoint at `/api/profiles/<username>/` returning all public fields in JSON format.

### Requirement 5: Developer Dashboard

**User Story:** As a User, I want a personalized dashboard that summarizes my activity, statistics, and quick actions, so that I can monitor my progress and navigate to key features efficiently.

#### Acceptance Criteria

1. WHEN an authenticated User navigates to the dashboard, THE System SHALL display: unread notification count, unread message count, problems posted count, solutions submitted count, accepted solutions count, applications sent count, pending connection requests count, current reputation score, and a quick-action panel.
2. THE System SHALL render a Chart.js chart on the dashboard showing the User's weekly and monthly solution submission statistics.
3. THE System SHALL display the Contribution_Graph on the dashboard reflecting the current year's activity by default.
4. THE System SHALL list the User's 5 most recent bookmarks on the dashboard with links to the bookmarked items.
5. THE System SHALL list the top 5 contributor Users by total accepted solutions in the dashboard leaderboard panel.
6. IF a User has zero solutions submitted, THE System SHALL display an empty-state panel with a call-to-action link to the problems list.
7. WHEN a User clicks a quick-action button (e.g., "Post a Problem", "Browse Opportunities", "View Messages"), THE System SHALL navigate the User to the corresponding page within 300 ms.
8. THE System SHALL update the unread notification count and unread message count in the dashboard header in real-time via WebSocket without requiring a full page reload.

### Requirement 6: Problems Module

**User Story:** As a User, I want to create, browse, and interact with technical problems, so that I can share challenges and discover interesting puzzles to solve.

#### Acceptance Criteria

1. WHEN an authenticated User submits a valid problem creation form with a title (3–255 characters), description (10+ characters in Markdown), difficulty level, and at most 5 tags, THE System SHALL create the Problem record and redirect the User to the problem detail page.
2. IF a User submits a problem creation form with a title shorter than 3 characters, THEN THE System SHALL reject the submission and return a validation error.
3. THE System SHALL render problem descriptions as formatted Markdown with Prism-based syntax highlighting on code blocks on the problem detail page.
4. WHEN a User adds a code block in the problem description using a fenced code block with a language identifier, THE System SHALL apply Prism syntax highlighting for that language on render.
5. THE System SHALL display on each problem detail page: the problem's title, description, difficulty badge, tags, author username with link to their Profile, creation date, view count, solution count, and related problems with shared tags.
6. THE System SHALL increment the view count of a Problem by 1 each time a unique User or Guest loads the problem detail page.
7. WHEN an authenticated User who is the author of a Problem submits an edit form, THE System SHALL update the Problem record and redirect to the updated detail page.
8. WHEN an authenticated User who is the author of a Problem confirms deletion, THE System SHALL delete the Problem and all associated Solutions, Comments, and Votes, then redirect to the problem list.
9. THE System SHALL support filtering problems by: difficulty (easy/medium/hard), tag, category, and sort order (newest, most viewed, most solved, most bookmarked).
10. WHEN a User searches problems using the search bar with a query of 1 or more characters, THE System SHALL return all Problems whose title or description contains the query string, case-insensitively, within 500 ms.
11. WHEN an authenticated User clicks "Bookmark" on a Problem, THE System SHALL create a Bookmark record for that User–Problem pair if one does not already exist, and update the bookmark button state immediately via JavaScript without a full page reload.
12. WHEN an authenticated User clicks "Unbookmark" on a previously bookmarked Problem, THE System SHALL delete the Bookmark record and update the button state immediately.
13. THE System SHALL allow a Problem author to attach up to 5 image files (JPEG, PNG, WebP; max 2 MB each) to a Problem as supporting attachments.
14. THE System SHALL expose a paginated problem list via the API at `/api/problems/` supporting query parameters: `q` (search), `difficulty`, `tag`, `ordering`.

### Requirement 7: Solutions Module

**User Story:** As a User, I want to submit, view, and manage solutions to problems, so that I can help others and demonstrate my skills.

#### Acceptance Criteria

1. WHEN an authenticated User submits a valid solution form for a Problem with at least an explanation (in Markdown) or a code block, THE System SHALL create the Solution record and redirect to the solution list for that Problem.
2. IF a User submits a solution form with both the explanation and code fields empty, THEN THE System SHALL reject the submission and return a validation error.
3. THE System SHALL render solution explanations as formatted Markdown and render code blocks with Monaco_Editor or Prism syntax highlighting, supporting at minimum: Python, JavaScript, TypeScript, Java, C, C++, Go, Rust.
4. THE System SHALL display solutions sorted by: accepted first, then by vote count descending, then by creation date descending (default), with an option to sort by newest only.
5. WHEN the Problem author clicks "Accept" on a Solution, THE System SHALL mark that Solution as accepted, remove the accepted status from any previously accepted Solution on the same Problem, and award reputation points to the Solution author.
6. WHEN an authenticated User submits a solution edit form for a Solution they authored, THE System SHALL save the updated explanation and code, record the edit in the Solution's edit history, and redirect to the solution list.
7. WHEN an authenticated User confirms deletion of their own Solution, THE System SHALL delete the Solution and all associated Comments and Votes, then redirect to the solution list.
8. WHEN an authenticated User clicks "Bookmark" on a Solution, THE System SHALL create a Bookmark record for that User–Solution pair if one does not exist, and update the bookmark button state immediately via JavaScript.
9. THE System SHALL expose a paginated solution list via the API at `/api/problems/<id>/solutions/` supporting sort parameter.
10. IF a User who is not the Solution author attempts to edit or delete the Solution via the web UI or API, THEN THE System SHALL return an authorization error and take no action.

### Requirement 8: Voting System

**User Story:** As a User, I want to upvote or downvote solutions, so that the community can surface the most helpful answers.

#### Acceptance Criteria

1. WHEN an authenticated User clicks "Upvote" on a Solution they have not previously voted on, THE System SHALL create a Vote record with type "upvote", increment the Solution's displayed vote count by 1, and award 10 reputation points to the Solution author.
2. WHEN an authenticated User clicks "Downvote" on a Solution they have not previously voted on, THE System SHALL create a Vote record with type "downvote", decrement the Solution's displayed vote count by 1, and deduct 2 reputation points from the Solution author.
3. WHEN an authenticated User who has previously upvoted a Solution clicks "Upvote" again, THE System SHALL remove the existing Vote record (toggle off), decrement the displayed vote count by 1, and reverse the 10 reputation points awarded.
4. WHEN an authenticated User who has previously downvoted a Solution clicks "Downvote" again, THE System SHALL remove the existing Vote record (toggle off), increment the displayed vote count by 1, and reverse the 2 reputation deduction.
5. WHEN an authenticated User who has previously voted on a Solution clicks the opposite vote button, THE System SHALL replace the existing Vote record with the new vote type and adjust the vote count and reputation by the combined delta.
6. THE System SHALL ensure each User can have at most one Vote record per Solution at any given time (enforced at the database level via unique constraint).
7. IF a Guest attempts to vote on a Solution, THEN THE System SHALL redirect the Guest to the login page.
8. THE System SHALL return the updated vote count and the User's current vote state in the AJAX response within 300 ms without a full page reload.
9. THE System SHALL prevent a User from voting on their own Solution by returning a validation error and taking no action.

### Requirement 9: Comments System

**User Story:** As a User, I want to post nested comments on solutions, react to comments, and use Markdown formatting, so that I can have structured discussions around solutions.

#### Acceptance Criteria

1. WHEN an authenticated User submits a comment form on a Solution with text between 1 and 2000 characters, THE System SHALL create a Comment record and re-render the comments section without a full page reload.
2. THE System SHALL support one level of nested replies — a Comment may have a parent Comment, and a reply may not itself have replies.
3. WHEN an authenticated User submits a reply to an existing Comment, THE System SHALL create a Comment record with the parent field set, and display the reply indented under the parent comment.
4. THE System SHALL render Comment text as Markdown with emoji shortcodes converted to Unicode emoji.
5. WHEN an authenticated User clicks "Edit" on their own Comment and submits updated text, THE System SHALL update the Comment record and display an "edited" label with the edit timestamp.
6. WHEN an authenticated User confirms deletion of their own Comment, THE System SHALL delete the Comment record and all replies, then update the comment section display.
7. WHEN an authenticated User clicks a reaction emoji on a Comment, THE System SHALL toggle the User's reaction of that type on the Comment and update the displayed reaction count via AJAX.
8. THE System SHALL support the following reactions per Comment: 👍 (thumbs_up), ❤️ (heart), 😄 (laugh), 🎉 (celebrate), 😮 (wow), 😢 (sad).
9. THE System SHALL allow a Problem's author to pin up to 1 Comment on each Solution as a "pinned comment", displayed first in the comments list.
10. IF a User who is not the Comment author attempts to edit or delete a Comment via the web UI or API, THEN THE System SHALL return an authorization error and take no action.

### Requirement 10: Connections and Follow System

**User Story:** As a User, I want to connect with other developers and follow profiles I find interesting, so that I can build my professional network.

#### Acceptance Criteria

1. WHEN an authenticated User sends an Invitation to another User via the invitation form, THE System SHALL create a pending Invitation record and send a real-time Notification to the receiver via WebSocket.
2. WHEN the receiving User accepts a pending Invitation, THE System SHALL update the Invitation status to "accepted", create a bidirectional Connection record between the two Users, send a Notification to the sender, and award 5 reputation points to both Users.
3. WHEN a User rejects a pending Invitation, THE System SHALL update the Invitation status to "rejected" and no Connection record is created.
4. WHEN a User cancels a pending Invitation they sent, THE System SHALL delete the Invitation record.
5. WHEN a User removes an existing Connection with another User, THE System SHALL delete the Connection record and update both Users' connection counts.
6. THE System SHALL display on the Connections page: the User's connections list, pending received invitations, and pending sent invitations.
7. THE System SHALL suggest up to 10 developers on the Connections page based on mutual connections count (descending), filtered to Users not already connected.
8. WHEN an authenticated User clicks "Follow" on another User's Profile, THE System SHALL create a Follow record if one does not exist, increment the followed User's follower count, and update the button state without a full page reload.
9. WHEN an authenticated User clicks "Unfollow" on a User they follow, THE System SHALL delete the Follow record, decrement the follower count, and update the button state.
10. THE System SHALL prevent a User from following or inviting themselves by returning a validation error.
11. THE System SHALL display mutual connections count on each suggested developer card.

### Requirement 11: Real-Time Chat

**User Story:** As a User, I want to exchange real-time messages with my connections, with typing indicators, read receipts, and file sharing, so that I can collaborate effectively.

#### Acceptance Criteria

1. WHEN two Users are connected (have a Connection record), THE System SHALL allow them to open a real-time chat room via WebSocket and exchange text messages with end-to-end delivery within 500 ms under normal network conditions.
2. IF a User who is not connected to the chat partner attempts to open the chat page, THEN THE System SHALL display a "not connected" error and redirect to the opportunities list.
3. WHEN a User is typing in the chat input and pauses for less than 3 seconds, THE System SHALL broadcast a typing indicator event to the other participant via WebSocket, displayed as "username is typing…".
4. WHEN a Message is delivered to the recipient's WebSocket connection, THE System SHALL update the Message record's delivered status to true.
5. WHEN the recipient opens the chat and loads a Message they have not previously read, THE System SHALL mark all such Messages as read and send a read-receipt event to the sender via WebSocket.
6. WHEN a User uploads an image (JPEG, PNG, WebP; max 5 MB) or a file (max 10 MB) in chat, THE System SHALL upload the file to the media storage backend, send the file URL as a Message, and display a preview for image files.
7. THE System SHALL display online/offline status and the last-seen timestamp for each User in the chat header, updated via WebSocket when Users connect or disconnect.
8. WHEN a User searches within a chat conversation using a search term of 1+ characters, THE System SHALL highlight all Messages in the conversation containing that term and scroll to the first match.
9. WHEN a User pins a Message in a conversation, THE System SHALL mark the Message as pinned and display it in a pinned-messages panel at the top of the chat.
10. THE System SHALL display an emoji picker that inserts Unicode emoji into the chat input field.
11. THE System SHALL paginate chat history, loading the 50 most recent Messages on initial load and fetching earlier Messages in batches of 50 when the User scrolls to the top.
12. THE System SHALL use Redis as the Channel Layer backend for all WebSocket consumers in production.

### Requirement 12: Notifications System

**User Story:** As a User, I want to receive real-time notifications for important events on the platform, so that I can stay informed without manually checking every page.

#### Acceptance Criteria

1. THE System SHALL deliver real-time Notifications to authenticated Users via WebSocket within 1 second of the triggering event.
2. THE System SHALL generate a Notification for the following events: (a) connection request received, (b) connection request accepted, (c) new comment on a User's Problem's Solution, (d) User's Solution accepted, (e) User's Solution upvoted or downvoted, (f) reply to a User's Comment, (g) new Message received, (h) Application status changed (accepted/rejected).
3. WHEN a User opens the Notification Center, THE System SHALL display all Notifications sorted by timestamp descending, with unread Notifications visually distinguished from read ones.
4. WHEN a User clicks "Mark all as read", THE System SHALL update all of the User's unread Notifications to read status and update the unread count badge to 0.
5. WHEN a User clicks a specific Notification, THE System SHALL mark it as read and navigate the User to the relevant resource (problem, solution, chat, application).
6. THE System SHALL display the unread Notification count as a badge on the notification bell icon in the navbar, updated in real-time via WebSocket.
7. THE System SHALL persist Notifications in the database so Users can view them after page reload.
8. WHEN a Notification is older than 90 days, THE Celery_Beat scheduler SHALL delete it via a periodic cleanup task.
9. THE System SHALL expose a Notification list via the API at `/api/notifications/` with mark-as-read PATCH support.

### Requirement 13: Opportunities Module

**User Story:** As a User, I want to post, browse, and manage job, internship, freelance, and open-source opportunities, so that I can find or offer relevant work.

#### Acceptance Criteria

1. WHEN an authenticated User submits a valid opportunity creation form with a title (3–255 characters), description (10+ characters), type (job/internship/freelance/open_source), required skills, and an optional deadline date, THE System SHALL create the Opportunity record and redirect to the opportunity detail page.
2. THE System SHALL display on the opportunity list page: title, type badge, required skills, creator username, creation date, application count, and active/closed status.
3. THE System SHALL support filtering opportunities by: type (job/internship/freelance/open_source), active status, and sorting by newest or most applications.
4. WHEN a User searches opportunities using a query of 1+ characters, THE System SHALL return all Opportunities whose title, description, or required skills contain the query, case-insensitively.
5. WHEN an authenticated User who is the Opportunity author submits an edit form, THE System SHALL update the Opportunity record and redirect to the updated detail page.
6. WHEN an authenticated User who is the Opportunity author confirms deletion, THE System SHALL soft-delete the Opportunity by setting is_active to false and return to the opportunity list.
7. WHEN an authenticated User who has not previously applied submits a valid application form (cover letter required; resume file optional; GitHub and portfolio URLs optional) for an active Opportunity, THE System SHALL create the Application record and display a confirmation toast notification.
8. IF a User attempts to apply to an Opportunity they have already applied to, THEN THE System SHALL return a validation error without creating a duplicate Application.
9. WHEN an authenticated User clicks "Bookmark" on an Opportunity, THE System SHALL create a Bookmark record and update the button state without a full page reload.
10. THE System SHALL expose a paginated opportunity list via the API at `/api/opportunities/` supporting query parameters: `q`, `type`, `ordering`.

### Requirement 14: Applications Module

**User Story:** As a User, I want to manage applications I send and receive, with clear status tracking and the ability to withdraw, so that I can organize my opportunity pipeline.

#### Acceptance Criteria

1. THE System SHALL display the Opportunity author's application management page listing all Applications for their Opportunities with: applicant username, cover letter preview, resume download link (if provided), GitHub link, portfolio link, submission date, and current status badge (pending/accepted/rejected).
2. WHEN an Opportunity author clicks "Accept" on a pending Application, THE System SHALL update the Application status to "accepted", send a real-time Notification to the applicant, and display a success toast.
3. WHEN an Opportunity author clicks "Reject" on a pending Application, THE System SHALL update the Application status to "rejected", send a real-time Notification to the applicant, and display a confirmation toast.
4. THE System SHALL display a separate "My Applications" page for applicants listing all Applications they submitted with: opportunity title, submission date, and current status badge.
5. WHEN an applicant clicks "Withdraw" on a pending Application they submitted, THE System SHALL delete the Application record and allow the User to reapply in the future.
6. IF an Opportunity author attempts to accept or reject an Application for an Opportunity they do not own, THEN THE System SHALL return an authorization error and take no action.
7. THE System SHALL support resume upload as a file (PDF; max 5 MB) stored in the media storage backend, distinct from the URL-only resume field in the existing model.

### Requirement 15: Bookmarks

**User Story:** As a User, I want to bookmark problems, solutions, and opportunities, so that I can quickly return to items I find valuable.

#### Acceptance Criteria

1. THE System SHALL support Bookmarks for three content types: Problem, Solution, and Opportunity.
2. WHEN an authenticated User bookmarks an item, THE System SHALL create a Bookmark record linking the User to the item with its content type, preventing duplicate bookmarks via a unique constraint on (user, content_type, object_id).
3. THE System SHALL display a "My Bookmarks" page listing all of a User's bookmarks grouped by type (Problems, Solutions, Opportunities) with links to the bookmarked items.
4. WHEN an authenticated User removes a bookmark, THE System SHALL delete the Bookmark record and update the displayed bookmark list without a full page reload.
5. THE System SHALL display the bookmark count on each Problem, Solution, and Opportunity detail page.
6. THE System SHALL expose the User's bookmarks via the API at `/api/bookmarks/` supporting GET (list) and DELETE (remove) operations.

### Requirement 16: Reputation System

**User Story:** As a User, I want to earn and lose reputation points through my contributions, so that my standing on the platform reflects my engagement and quality of work.

#### Acceptance Criteria

1. THE System SHALL maintain a numeric reputation score for each User initialized at 0 upon registration.
2. THE System SHALL award or deduct reputation points for the following events (listed as event → delta): Solution upvoted → +10; Solution downvoted → -2; Solution accepted → +25; Problem posted → +5; Comment posted → +2; Connection established → +5 (both Users); Vote removed (upvote toggled off) → -10; Vote removed (downvote toggled off) → +2.
3. THE System SHALL assign a reputation level to each User based on their current score: 0–99 → Beginner; 100–499 → Contributor; 500–1499 → Expert; 1500–4999 → Mentor; 5000+ → Legend.
4. THE System SHALL display the User's current reputation score and level on their Profile page and dashboard.
5. THE System SHALL award Badges automatically when a User reaches the following milestones (badge → trigger): "First Solution" → first Solution submitted; "Problem Solver" → 10 accepted Solutions; "Community Builder" → 50 Connections; "Upvote Magnet" → 100 upvotes received; and "Top Contributor" → reaching the Expert level.
6. THE System SHALL display earned Badges on the User's Profile page with the badge name, icon, and date awarded.
7. WHEN a reputation-altering event occurs, THE System SHALL update the User's reputation score atomically to prevent race conditions under concurrent requests.
8. THE System SHALL expose the User's reputation history (event, delta, timestamp) via the API at `/api/reputation/history/`.

### Requirement 17: Global Search

**User Story:** As a User, I want to search across the entire platform for developers, problems, solutions, and opportunities from a single search bar, so that I can find relevant content quickly.

#### Acceptance Criteria

1. THE System SHALL provide a global search bar visible in the navbar for all authenticated Users.
2. WHEN a User types a query of 2+ characters in the global search bar, THE System SHALL return autocomplete suggestions within 300 ms, grouping results by category: Developers, Problems, Solutions, Opportunities, Tags.
3. WHEN a User submits a global search query of 1+ characters, THE System SHALL display a search results page with results grouped by category, showing at most 10 results per category on initial load.
4. THE System SHALL support filtering the search results page by category (Developers, Problems, Solutions, Opportunities) and by sort order (relevance, newest).
5. THE System SHALL highlight the search query term within displayed result excerpts.
6. IF a search query yields zero results in a category, THE System SHALL display an empty-state message for that category rather than hiding it entirely.
7. THE System SHALL expose a unified search API endpoint at `/api/search/` accepting `q`, `type` (developer/problem/solution/opportunity), and `ordering` parameters, returning paginated results.

### Requirement 18: REST API

**User Story:** As a developer, I want a fully documented REST API with JWT authentication and consistent pagination, so that I can build integrations or mobile clients on top of DevLink.

#### Acceptance Criteria

1. THE System SHALL expose all major resources (users, profiles, problems, solutions, comments, votes, opportunities, applications, connections, notifications, bookmarks, search) as versioned REST API endpoints under the `/api/v1/` prefix.
2. THE System SHALL protect all write endpoints (POST, PUT, PATCH, DELETE) with JWT authentication, returning HTTP 401 for unauthenticated requests and HTTP 403 for unauthorized requests.
3. THE System SHALL paginate all list API endpoints using cursor-based or page-number pagination, returning `count`, `next`, `previous`, and `results` fields in the response body.
4. THE System SHALL support filtering and ordering on list endpoints via query parameters as documented in the OpenAPI schema.
5. THE System SHALL generate an OpenAPI 3.0 schema and serve interactive Swagger UI documentation at `/api/docs/` and ReDoc at `/api/redoc/` using drf_spectacular.
6. THE System SHALL validate all API request bodies against their Serializer schema, returning HTTP 400 with a structured error body on validation failure.
7. THE System SHALL use consistent HTTP status codes: 200 for successful reads, 201 for successful creates, 204 for successful deletes, 400 for validation errors, 401 for authentication errors, 403 for authorization errors, 404 for not-found resources.
8. THE System SHALL include rate limiting on all API endpoints: 100 requests per minute per authenticated User, 20 requests per minute per unauthenticated IP.
9. THE System SHALL version the API so that `/api/v1/` endpoints are independent of any future `/api/v2/` endpoints.

### Requirement 19: UI/UX — Bootstrap 5, Dark Mode, Animations, and Accessibility

**User Story:** As a User, I want a modern, responsive, accessible interface with dark mode support and smooth visual feedback, so that I enjoy using the platform across devices.

#### Acceptance Criteria

1. THE System SHALL migrate the frontend from Tailwind CDN to Bootstrap 5, Bootstrap Icons, and a compiled static CSS bundle, ensuring all existing pages render correctly after migration.
2. THE System SHALL provide a dark mode / light mode toggle in the navbar that persists the User's preference in localStorage and applies the correct color scheme on page load without flash.
3. WHEN page data is loading (initial page load or AJAX fetch), THE System SHALL display Bootstrap-compatible skeleton loader placeholders in place of content areas, replaced by actual content when the data is ready.
4. THE System SHALL display Toastify.js toast notifications for all user-facing success, warning, and error events, positioned in the bottom-right corner, auto-dismissing after 4 seconds.
5. THE System SHALL apply AOS scroll-based entry animations (fade-up, 400 ms duration) to card elements on the homepage, problem list, and opportunity list pages.
6. THE System SHALL include dedicated 404 and 500 error pages matching the DevLink visual design, with a link back to the homepage.
7. THE System SHALL be fully responsive, with layouts functioning correctly on viewports from 320 px (mobile) to 1440 px (desktop).
8. THE System SHALL meet WCAG 2.1 Level AA requirements, including: sufficient color contrast ratios (4.5:1 for normal text, 3:1 for large text), keyboard navigability for all interactive elements, ARIA labels on icon-only buttons, and alt text on all informational images.
9. THE System SHALL display meaningful empty-state illustrations or messages on all list pages when no items are present.

### Requirement 20: Security

**User Story:** As the platform operator, I want DevLink to enforce comprehensive security controls, so that user data is protected and the system is resistant to common web attacks.

#### Acceptance Criteria

1. THE System SHALL enforce RBAC on all views and API endpoints, verifying that the requesting User has the required permission (owner, connected, authenticated, or public) before processing any action.
2. THE System SHALL include Django's CSRF middleware on all non-API state-mutating web views, and validate CSRF tokens on all POST/PUT/PATCH/DELETE form submissions.
3. THE System SHALL use parameterized ORM queries exclusively and never construct raw SQL strings from user-supplied input.
4. THE System SHALL sanitize all user-supplied HTML content (e.g., Markdown-rendered output) using a server-side allowlist sanitizer before rendering in templates, to prevent stored XSS attacks.
5. THE System SHALL set the following HTTP security headers on all responses: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy` (restrictive policy), `Strict-Transport-Security` (HTTPS-only in production), `Referrer-Policy: same-origin`.
6. THE System SHALL validate all file uploads for: MIME type (whitelist), file size limit, and filename sanitization, rejecting uploads that fail any check with a descriptive error.
7. THE System SHALL log all security-sensitive events to the Audit_Log with: event type, user ID or IP, timestamp, and resource affected.
8. WHEN a User accesses a resource they are not authorized to view or modify, THE System SHALL return HTTP 403 (API) or redirect to an error page (web UI) without revealing whether the resource exists.
9. THE System SHALL apply Rate_Limiter middleware to all authentication endpoints: maximum 5 attempts per IP per 10-minute window.
10. THE System SHALL enforce HTTPS in the production Docker configuration via Nginx and redirect all HTTP requests to HTTPS.

### Requirement 21: Infrastructure and Deployment

**User Story:** As the platform operator, I want a Dockerized deployment with PostgreSQL, Redis, Celery, Nginx, and Gunicorn, so that the application runs reliably and can be scaled in production.

#### Acceptance Criteria

1. THE System SHALL include a `docker-compose.yml` defining services for: `web` (Django/Gunicorn), `nginx`, `postgres`, `redis`, `celery_worker`, and `celery_beat`, with all inter-service dependencies declared.
2. THE System SHALL read all secrets and environment-specific configuration (SECRET_KEY, DATABASE_URL, REDIS_URL, email credentials, AWS/media storage keys) from environment variables and never commit them to source control.
3. THE System SHALL provide a `.env.example` file documenting all required environment variables.
4. THE System SHALL use PostgreSQL as the database backend in production, configured via the `DATABASE_URL` environment variable, while retaining SQLite as the default for local development without Docker.
5. THE System SHALL use Redis as the Django Channels channel layer backend and as the Celery broker in production, configured via the `REDIS_URL` environment variable.
6. THE System SHALL configure Celery to use Redis as the broker and result backend, with a Celery Beat schedule for periodic tasks (notification cleanup, statistics aggregation).
7. THE System SHALL serve Django static files and media files via Nginx in production, with Django's `STATIC_ROOT` and `MEDIA_ROOT` mapped to Nginx-served directories.
8. THE System SHALL include environment-split settings: `settings/base.py`, `settings/development.py`, and `settings/production.py`, selected via the `DJANGO_SETTINGS_MODULE` environment variable.
9. THE System SHALL apply all database migrations automatically during the Docker entrypoint script before starting Gunicorn.
10. THE System SHALL configure Gunicorn with a minimum of 2 worker processes and a 30-second timeout in the production Docker service definition.

### Requirement 22: Admin Panel

**User Story:** As a platform administrator, I want a comprehensive Django admin interface with analytics, content moderation, and user management, so that I can operate and monitor the platform.

#### Acceptance Criteria

1. THE System SHALL register all models (User/Profile, Problem, Tag, Solution, Vote, Comment, Opportunity, Application, Invitation, Connection, Message, Notification, Bookmark, Badge, ReputationEvent) in the Django admin with appropriate list_display, search_fields, and list_filter configurations.
2. THE System SHALL provide a custom admin dashboard page at `/admin/` displaying site-wide analytics: total users, total problems, total solutions, new registrations in the last 7 days, total connections, and total messages.
3. WHEN an administrator activates or deactivates a User account from the admin, THE System SHALL update the User's `is_active` flag and log the action to the Audit_Log.
4. THE System SHALL allow administrators to delete any Problem, Solution, Comment, or Opportunity from the admin, with the deletion cascading to associated records.
5. THE System SHALL allow administrators to view and export all Audit_Log entries, filtered by event type and date range.
6. THE System SHALL allow administrators to manually award or revoke Badges from User profiles via the admin interface.

### Requirement 23: Non-Functional Requirements — Performance

**User Story:** As a User, I want the platform to respond quickly under typical load, so that I can use it without frustrating delays.

#### Acceptance Criteria

1. THE System SHALL serve all server-rendered HTML pages with a Time to First Byte (TTFB) of less than 500 ms for authenticated requests under a load of 50 concurrent users.
2. THE System SHALL serve all API list endpoints with a response time of less than 300 ms for paginated responses of up to 20 items under a load of 50 concurrent users.
3. THE System SHALL deliver WebSocket messages (chat and notifications) to connected clients within 1 second under normal network conditions.
4. THE System SHALL use database query optimization (select_related, prefetch_related, database indexes on frequently queried foreign key and filter fields) to prevent N+1 queries on list views.
5. THE System SHALL paginate all list views (problems, solutions, opportunities, users) at a default page size of 20 items, with a maximum page size of 100 items.

### Requirement 24: Non-Functional Requirements — Scalability and Maintainability

**User Story:** As the development team, I want the codebase to be modular, well-tested, and structured for growth, so that new features can be added without breaking existing functionality.

#### Acceptance Criteria

1. THE System SHALL organize each Django app with dedicated modules: `models.py`, `views.py`, `urls.py`, `forms.py`, `services.py`, `selectors.py`, `permissions.py`, `serializers.py`, `signals.py`, `validators.py`, `tests.py`, `admin.py`.
2. THE System SHALL maintain test coverage of at least 80% for all service and selector layer functions.
3. THE System SHALL define Serializer classes for all API resources, with nested serializers for related objects where appropriate.
4. WHEN a Celery task fails after 3 retry attempts, THE System SHALL log the failure with task name, arguments, and exception traceback to the application log.
5. THE System SHALL use Django signals exclusively for cross-app side effects (e.g., creating a Profile on User creation, awarding badges on reputation events) to avoid direct cross-app imports between services.

### Requirement 25: Markdown Parsing and Pretty-Printing (Parser Round-Trip)

**User Story:** As a User, I want my Markdown content (in problems, solutions, and comments) to render correctly and consistently, so that code blocks and formatting display as intended.

#### Acceptance Criteria

1. WHEN a User submits Markdown content, THE System SHALL parse the Markdown string into a structured representation using the server-side Markdown parser.
2. THE System SHALL render parsed Markdown into safe HTML, sanitizing the output to an allowlist of permitted tags (p, h1–h6, ul, ol, li, strong, em, code, pre, blockquote, a, img) and stripping all script, style, and event-handler attributes.
3. THE Pretty_Printer SHALL format internal Markdown AST representations back into valid Markdown text for storage and re-rendering.
4. FOR ALL valid Markdown strings submitted by Users, parsing then rendering then parsing the rendered output SHALL produce semantically equivalent content (round-trip property: no data loss between parse → render → parse).
5. WHEN a User submits a Markdown string containing a fenced code block with a language identifier, THE System SHALL apply Prism.js syntax highlighting for that language in the rendered output.

### Requirement 26: Session Management and Login History

**User Story:** As a User, I want to view my active login sessions and recently logged-in devices, so that I can detect unauthorized access and revoke sessions I don't recognize.

#### Acceptance Criteria

1. THE System SHALL record each successful login in a LoginEvent record containing: user, IP address, user-agent string, timestamp, and session key.
2. THE System SHALL display the User's login history page at `/accounts/security/` listing the 20 most recent LoginEvent records for that User.
3. WHEN an authenticated User clicks "Revoke" on an active session from the login history page, THE System SHALL delete the associated Django session record and redirect the User to the login history page.
4. THE System SHALL display an indicator on the login history page showing which session is the current one.
5. IF the User's account is accessed from a new IP address or user-agent not seen in the previous 30 days, THE System SHALL send a security alert email to the User asynchronously via Celery.

### Requirement 27: Email Notifications (Asynchronous)

**User Story:** As a User, I want to receive email notifications for critical account and platform events, so that I stay informed even when I'm not actively using the platform.

#### Acceptance Criteria

1. THE System SHALL send all transactional emails asynchronously via Celery tasks to prevent blocking web request handling.
2. THE System SHALL send an email to a User when: (a) their account is created (activation link), (b) their password is reset, (c) their Application is accepted or rejected, (d) a new login from an unrecognized device is detected.
3. THE System SHALL use HTML email templates consistent with the DevLink visual style, with plain-text fallback versions.
4. IF a Celery email task fails on first attempt, THE System SHALL retry the task up to 3 times with exponential backoff (delays: 60 s, 300 s, 900 s) before marking the task as failed.
5. THE System SHALL not expose internal system errors or stack traces in any user-facing email content.

---

## Correctness Properties (Property-Based Testing)

The following properties are suitable for property-based testing. They are derived from the acceptance criteria above and describe invariants, round-trips, and metamorphic properties of the system's core logic.

### P1: Vote Count Invariant

**Derived from:** Requirement 8 (Voting System)

For any Solution with an arbitrary set of Vote records:

- **Invariant:** `solution.net_vote_count == (upvote_count - downvote_count)` at all times.
- **Metamorphic:** After a User casts an upvote then removes it (toggle), the Solution's net vote count SHALL equal its count before the upvote was cast.
- **Uniqueness:** For any (user, solution) pair, at most one Vote record SHALL exist in the database at any time regardless of concurrent voting operations.

### P2: Reputation Score Invariant

**Derived from:** Requirement 16 (Reputation System)

For any sequence of reputation-altering events applied to a User:

- **Invariant:** `user.reputation_score == sum(event.delta for event in user.reputation_events)` at all times.
- **Idempotence:** Applying the same reputation event twice (e.g., duplicate task execution) SHALL NOT change the reputation score — each event record is unique and guarded by a unique constraint.
- **Monotonicity of level:** A User's reputation level SHALL never downgrade unless the reputation score numerically falls below the level's lower bound.

### P3: Connection Bidirectionality

**Derived from:** Requirement 10 (Connections)

For any two Users A and B:

- **Invariant:** `is_connected(A, B) == is_connected(B, A)` — connectivity is symmetric.
- **Round-trip:** If User A sends an Invitation to User B, User B accepts it, and then User A removes the Connection, the result SHALL be identical to the initial state (no Connection, no pending Invitation between A and B).
- **No self-connection:** For all Users U, `Connection.objects.filter(user1=U, user2=U).count() == 0`.

### P4: Bookmark Idempotence

**Derived from:** Requirement 15 (Bookmarks)

For any User and any bookmarkable content item (Problem, Solution, Opportunity):

- **Idempotence:** Bookmarking the same item twice SHALL result in exactly one Bookmark record (the second operation is a no-op or returns the existing record).
- **Invariant after removal:** After unbookmarking an item, `Bookmark.objects.filter(user=U, object_id=item.id).count() == 0`.

### P5: Markdown Round-Trip

**Derived from:** Requirement 25 (Markdown Parsing and Pretty-Printing)

For all valid Markdown strings S:

- **Round-trip:** `parse(render(parse(S))) ≡ parse(S)` — parsing and rendering produces semantically equivalent structure with no content loss.
- **Safety:** The rendered HTML output of any Markdown string SHALL NOT contain `<script>`, `<style>`, or `on*=` event handler attributes.

### P6: Pagination Completeness

**Derived from:** Requirement 18 (REST API), Requirements 6, 7, 13

For any paginated API list endpoint with N total items and page size P:

- **Invariant:** Iterating through all pages by following `next` links SHALL visit exactly N unique items in total — no duplicates, no omissions.
- **Stability:** For any ordering parameter, the total item count across all pages SHALL equal the count returned in the `count` field of the first page.

### P7: Unique Vote per (User, Solution)

**Derived from:** Requirement 8, Acceptance Criterion 6

For any arbitrary sequence of vote and un-vote operations by User U on Solution S:

- **Invariant:** At any point in time, `Vote.objects.filter(user=U, solution=S).count() <= 1`.

### P8: Solution Accept Exclusivity

**Derived from:** Requirement 7, Acceptance Criterion 5

For any Problem P at any point in time:

- **Invariant:** `Solution.objects.filter(problem=P, is_accepted=True).count() <= 1` — at most one Solution per Problem may be accepted simultaneously.

### P9: Notification Delivery Ordering

**Derived from:** Requirement 12 (Notifications)

For any User receiving a sequence of N notification events:

- **Invariant:** The Notification Center SHALL display all N notifications.
- **Ordering:** Notifications SHALL be returned sorted by timestamp descending — for any two Notifications A and B where A was created after B, A appears before B in the list.

### P10: JWT Token Round-Trip

**Derived from:** Requirement 2 (Authentication)

For any valid User credentials (username, password):

- **Round-trip:** `decode(encode(user)) == user` — the JWT payload encoded during login, when decoded with the correct secret, SHALL return the same user_id without modification.
- **Expiry:** A JWT access token decoded after its lifetime (60 minutes) SHALL raise a token-expired error and SHALL NOT authenticate the User.
