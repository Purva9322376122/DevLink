from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verb', models.CharField(
                    choices=[
                        ('connection_request', 'Connection Request'),
                        ('connection_accepted', 'Connection Accepted'),
                        ('new_message', 'New Message'),
                        ('solution_commented', 'Solution Commented'),
                        ('comment_replied', 'Comment Replied'),
                        ('solution_accepted', 'Solution Accepted'),
                        ('solution_upvoted', 'Solution Upvoted'),
                        ('application_received', 'Opportunity Application'),
                        ('application_accepted', 'Application Accepted'),
                        ('application_rejected', 'Application Rejected'),
                    ],
                    db_index=True,
                    max_length=30,
                )),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('target_url', models.CharField(blank=True, max_length=500)),
                ('preview', models.CharField(blank=True, max_length=200)),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='acted_notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('content_type', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    to='contenttypes.contenttype',
                )),
                ('recipient', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['recipient', 'is_read', '-created_at'],
                name='notif_recipient_read_idx',
            ),
        ),
    ]
