# Generated migration to add database indexes for frequently queried fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_transaction_checkout_request_id'),
    ]

    operations = [
        # Transaction model indexes
        migrations.AlterField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='events.user', db_index=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='events.event', db_index=True),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['status'], name='payments_transaction_status_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['timestamp'], name='payments_transaction_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['payment_method'], name='payments_transaction_payment_method_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user', 'status'], name='payments_transaction_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['status', 'timestamp'], name='payments_transaction_status_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['event', 'status'], name='payments_transaction_event_status_idx'),
        ),
    ]
