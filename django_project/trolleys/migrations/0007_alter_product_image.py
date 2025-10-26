# Generated migration to change image field to image_url

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trolleys', '0006_remove_specificationitem_unique_spec_item_per_drawer_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
        migrations.AddField(
            model_name='product',
            name='image_url',
            field=models.URLField(blank=True, help_text='URL de la imagen del artículo', null=True),
        ),
    ]
