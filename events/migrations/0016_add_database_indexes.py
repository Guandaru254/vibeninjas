# Generated migration to add database indexes for frequently queried fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0015_event_slug'),
    ]

    operations = [
        # Event model indexes
        migrations.AlterField(
            model_name='event',
            name='organizer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='events.user', db_index=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='events.category', db_index=True),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['is_active'], name='events_event_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['date'], name='events_event_date_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['created_at'], name='events_event_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['organizer', 'is_active'], name='events_event_organizer_active_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['category', 'is_active', 'date'], name='events_event_category_active_date_idx'),
        ),
        
        # TicketCategory model indexes
        migrations.AlterField(
            model_name='ticketcategory',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_categories', to='events.event', db_index=True),
        ),
        migrations.AddIndex(
            model_name='ticketcategory',
            index=models.Index(fields=['is_free'], name='events_ticketcategory_is_free_idx'),
        ),
        migrations.AddIndex(
            model_name='ticketcategory',
            index=models.Index(fields=['available_tickets'], name='events_ticketcategory_available_tickets_idx'),
        ),
        migrations.AddIndex(
            model_name='ticketcategory',
            index=models.Index(fields=['event', 'available_tickets'], name='events_ticketcategory_event_available_idx'),
        ),
        
        # Merchandise model indexes (from models_merchandise.py)
        migrations.AlterField(
            model_name='merchandise',
            name='seller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='merchandise', to='events.user', db_index=True),
        ),
        migrations.AlterField(
            model_name='merchandise',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='events.merchandisecategory', db_index=True),
        ),
        migrations.AddIndex(
            model_name='merchandise',
            index=models.Index(fields=['status'], name='events_merchandise_status_idx'),
        ),
        migrations.AddIndex(
            model_name='merchandise',
            index=models.Index(fields=['created_at'], name='events_merchandise_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='merchandise',
            index=models.Index(fields=['seller', 'status'], name='events_merchandise_seller_status_idx'),
        ),
        migrations.AddIndex(
            model_name='merchandise',
            index=models.Index(fields=['category', 'status'], name='events_merchandise_category_status_idx'),
        ),
        migrations.AddIndex(
            model_name='merchandise',
            index=models.Index(fields=['seller_type'], name='events_merchandise_seller_type_idx'),
        ),
        
        # MerchandiseOrder model indexes
        migrations.AlterField(
            model_name='merchandiseorder',
            name='buyer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='merchandise_orders', to='events.user', db_index=True),
        ),
        migrations.AddIndex(
            model_name='merchandiseorder',
            index=models.Index(fields=['status'], name='events_merchandiseorder_status_idx'),
        ),
        migrations.AddIndex(
            model_name='merchandiseorder',
            index=models.Index(fields=['created_at'], name='events_merchandiseorder_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='merchandiseorder',
            index=models.Index(fields=['buyer', 'status'], name='events_merchandiseorder_buyer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='merchandiseorder',
            index=models.Index(fields=['status', 'created_at'], name='events_merchandiseorder_status_created_idx'),
        ),
    ]
