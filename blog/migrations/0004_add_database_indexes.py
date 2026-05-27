# Generated migration to add database indexes for frequently queried fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_alter_category_icon'),
    ]

    operations = [
        # Post model indexes
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blog_posts', to='events.user', db_index=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='posts', to='blog.category', db_index=True),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['is_published'], name='blog_post_is_published_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['created_at'], name='blog_post_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['is_published', 'created_at'], name='blog_post_published_created_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['author', 'is_published'], name='blog_post_author_published_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['category', 'is_published'], name='blog_post_category_published_idx'),
        ),
    ]
