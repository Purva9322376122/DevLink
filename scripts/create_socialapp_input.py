from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
site = Site.objects.get(pk=1)
app, created = SocialApp.objects.get_or_create(provider='google', defaults={'name':'DevLink Google', 'client_id':'', 'secret':''})
if site not in app.sites.all():
    app.sites.add(site)
    app.save()
print('SocialApp created or exists:', app, 'created=', created)
