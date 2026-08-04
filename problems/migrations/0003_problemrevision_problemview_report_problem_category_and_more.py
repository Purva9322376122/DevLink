# Generated migration — Phase 5 additions
# Modified to handle existing Tag records by populating slugs before
# enforcing the unique constraint.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils.text import slugify


def populate_tag_slugs(apps, schema_editor):
    """Give every existing Tag a unique slug derived from its name."""
    Tag = apps.get_model('problems', 'Tag')
    for tag in Tag.objects.all():
        base = slugify(tag.name) or tag.name.lower().replace(' ', '-')
        slug = base
        counter = 1
        while Tag.objects.filter(slug=slug).exclude(pk=tag.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1
        tag.slug = slug
        tag.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0002_tag_alter_problem_difficulty_alter_problem_user_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── New models ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='ProblemRevision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('difficulty', models.CharField(max_length=10)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-version']},
        ),
        migrations.CreateModel(
            name='ProblemView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(
                    choices=[('problem', 'Problem'), ('solution', 'Solution'), ('comment', 'Comment')],
                    db_index=True, max_length=20,
                )),
                ('object_id', models.PositiveIntegerField()),
                ('reason', models.CharField(
                    choices=[('spam', 'Spam'), ('offensive', 'Offensive'), ('duplicate', 'Duplicate'),
                             ('incorrect', 'Incorrect Information'), ('other', 'Other')],
                    max_length=20,
                )),
                ('description', models.TextField(blank=True)),
                ('is_resolved', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={'ordering': ['-created_at']},
        ),

        # ── Problem field additions ───────────────────────────────────────
        migrations.AddField(model_name='problem', name='category',
            field=models.CharField(blank=True, db_index=True, max_length=100)),
        migrations.AddField(model_name='problem', name='is_deleted',
            field=models.BooleanField(db_index=True, default=False)),
        migrations.AddField(model_name='problem', name='language',
            field=models.CharField(blank=True, db_index=True, max_length=50)),
        migrations.AddField(model_name='problem', name='updated_at',
            field=models.DateTimeField(auto_now=True)),
        migrations.AddField(model_name='problem', name='view_count',
            field=models.PositiveIntegerField(db_index=True, default=0)),

        # ── Tag field additions (slug non-unique first) ───────────────────
        migrations.AddField(model_name='tag', name='description',
            field=models.TextField(blank=True)),
        migrations.AddField(model_name='tag', name='slug',
            # Start as NOT unique so existing rows can coexist
            field=models.SlugField(blank=True, unique=False, default='')),
        migrations.AddField(model_name='tag', name='usage_count',
            field=models.PositiveIntegerField(db_index=True, default=0)),

        # ── Data migration: populate slugs ────────────────────────────────
        migrations.RunPython(populate_tag_slugs, migrations.RunPython.noop),

        # ── Now enforce uniqueness ────────────────────────────────────────
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(blank=True, unique=True),
        ),

        # ── Alter existing fields ─────────────────────────────────────────
        migrations.AlterField(model_name='problem', name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True)),
        migrations.AlterField(model_name='problem', name='difficulty',
            field=models.CharField(
                choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
                db_index=True, default='easy', max_length=10,
            )),
        migrations.AlterField(model_name='problem', name='title',
            field=models.CharField(db_index=True, max_length=255)),
        migrations.AlterField(model_name='problem', name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='problems', to=settings.AUTH_USER_MODEL,
            )),

        # ── Composite indexes ─────────────────────────────────────────────
        migrations.AddIndex(model_name='problem',
            index=models.Index(fields=['difficulty', 'created_at'],
                               name='problems_pr_difficu_af43a2_idx')),
        migrations.AddIndex(model_name='problem',
            index=models.Index(fields=['is_deleted', '-created_at'],
                               name='problems_pr_is_dele_f8168b_idx')),

        # ── FK additions ──────────────────────────────────────────────────
        migrations.AddField(model_name='problemrevision', name='editor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='problemrevision', name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='revisions', to='problems.problem')),
        migrations.AddField(model_name='problemview', name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='problem_views', to='problems.problem')),
        migrations.AddField(model_name='problemview', name='user',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='report', name='reporter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='reports_filed', to=settings.AUTH_USER_MODEL)),
        migrations.AddIndex(model_name='problemview',
            index=models.Index(fields=['problem', 'viewed_at'],
                               name='problems_pr_problem_19dfc9_idx')),
        migrations.AlterUniqueTogether(name='report',
            unique_together={('reporter', 'content_type', 'object_id')}),
    ]
