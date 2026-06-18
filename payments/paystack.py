"""
Paystack Payment Integration
============================
Location: payments/paystack.py
"""
import json
import requests
from django.conf import settings


def checkout(payload):
    """
    Initialize a Paystack checkout session.
    
    Args:
        payload (dict): Payment data including email, amount, reference, etc.
        
    Returns:
        tuple: (success: bool, authorization_url_or_error_message: str)
    """
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        'https://api.paystack.co/transaction/initialize',
        headers=headers, 
        data=json.dumps(payload)
    )
    response_data = response.json() 

    if response_data.get('status') == True:
        return True, response_data['data']['authorization_url']
    else:
        return False, "Failed to initiate payment, please try again later."
