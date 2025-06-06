# Generated by Django 5.1.5 on 2025-04-04 06:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CodeContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('html_code', models.TextField()),
                ('css_code', models.TextField(blank=True, null=True)),
                ('js_code', models.TextField(blank=True, null=True)),
                ('image_preview', models.ImageField(upload_to='code_previews/')),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=6)),
                ('category', models.CharField(choices=[('web', 'Web Design'), ('backend', 'Backend Development'), ('data', 'Data Science'), ('utility', 'Utility Scripts'), ('other', 'Other')], default='other', max_length=50)),
                ('difficulty', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner', max_length=20)),
                ('tags', models.CharField(blank=True, help_text='Comma-separated tags', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('developer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
