# Generated by Django 5.1.5 on 2025-04-19 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_remove_codecontent_tags_alter_codecontent_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='codecontent',
            name='category',
            field=models.CharField(choices=[('card', 'Cards'), ('checkbox', 'Checkbox'), ('button', 'Button'), ('switch', 'Switch'), ('icon', 'Icon'), ('form', 'Form'), ('toggle', 'Toggle'), ('input', 'Input'), ('slider', 'Slider'), ('dropdown', 'Dropdown'), ('modal', 'Modal'), ('accordion', 'Accordion'), ('tabs', 'Tabs'), ('alert', 'Alert'), ('hover', 'Hover'), ('responsive', 'Responsive'), ('other', 'Other')], default='other', max_length=50),
        ),
    ]
