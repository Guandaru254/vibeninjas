# Generated migration to add database indexes for frequently queried fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seller_merchandise', '0003_alter_sellermerchandise_id_and_more'),
    ]

    operations = [
        # SellerMerchandise model indexes
        migrations.AlterField(
            model_name='sellermerchandise',
            name='seller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_merchandise', to='events.user', db_index=True),
        ),
        migrations.AlterField(
            model_name='sellermerchandise',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='seller_merchandise.sellermerchandisecategory', db_index=True),
        ),
        migrations.AddIndex(
            model_name='sellermerchandise',
            index=models.Index(fields=['status'], name='seller_merchandise_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sellermerchandise',
            index=models.Index(fields=['created_at'], name='seller_merchandise_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='sellermerchandise',
            index=models.Index(fields=['seller', 'status'], name='seller_merchandise_seller_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sellermerchandise',
            index=models.Index(fields=['category', 'status'], name='seller_merchandise_category_status_idx'),
        ),
        
        # SellerMerchandiseOrder model indexes
        migrations.AlterField(
            model_name='sellermerchandiseorder',
            name='buyer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_merchandise_orders', to='events.user', db_index=True),
        ),
        migrations.AlterField(
            model_name='sellermerchandiseorder',
            name='seller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_orders', to='events.user', db_index=True),
        ),
        migrations.AddIndex(
            model_name='sellermerchandiseorder',
            index=models.Index(fields=['status'], name='seller_merchandise_order_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sellermerchandiseorder',
            index=models.Index(fields=['created_at'], name='seller_merchandise_order_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='sellermerchandiseorder',
            index=models.Index(fields=['buyer', 'status'], name='seller_merchandise_order_buyer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='sellermerchandiseorder',
            index=models.Index(fields=['seller', 'status'], name='seller_merchandise_order_seller_status_idx'),
        ),
    ]
