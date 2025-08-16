import requests
from django.core.cache import cache
from django.conf import settings
import threading
from django.template.loader import render_to_string


def get_member_details_by_card(card_number):
    try:
        response = requests.get(settings.AUTH_SERVER_URL + "/cardno/member-details/", params={"card_number": card_number})
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error contacting auth service: {e}")
        return None
    
    
def get_member_details_by_mobile_number(mobile_number):
    try:
        response = requests.get(settings.AUTH_SERVER_URL + "/member-details/", params={"mobile_number": mobile_number})
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error contacting auth service: {e}")
        return None
    
    
# AUTH_SERVICE_BUSINESS_URL = settings.AUTH_SERVER_URL + "/business/details/",

def get_business_details_by_id(business_id):
    try:
        response = requests.get(settings.AUTH_SERVER_URL + "/business/details/", params={"business_id": business_id})
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error contacting auth service: {e}")
        return None





def send_template_email(subject, template_name, context, recipient_list, attachments=None):
    """
    Send an email by invoking your AWS Lambda SES API.
    Supports HTML content and optional attachments.
    """
    # Render the HTML content
    html_message = render_to_string(template_name, context)

    sender = "contact@jsjcard.com"  # Your verified SES sender email
    recipient = recipient_list[0] if recipient_list else None

    if not recipient:
        print("No recipient provided.")
        return

    api_url = "https://w1yg18jn76.execute-api.ap-south-1.amazonaws.com/default/sesapi"

    # Prepare payload
    payload = {
        "sender": sender,
        "recipient": recipient,
        "subject": subject,
        "body": html_message
    }

    # If attachments are provided, encode them as JSON string
    if attachments:
        payload["attachments"] = attachments  # Must be a list of dicts as per your Lambda spec

    headers = {"Content-Type": "application/json"}

    def send_email():
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                print("✅ Email sent successfully via AWS SES API.")
            else:
                print(f"❌ Failed to send email. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception while sending email: {e}")

    threading.Thread(target=send_email).start()


