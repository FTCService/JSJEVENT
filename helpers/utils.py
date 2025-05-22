import random
import requests
from django.core.cache import cache
import urllib.parse
import pytz
from datetime import datetime
from django.conf import settings


def get_member_details_by_card(card_number):
    try:
        response = requests.get(settings.AUTH_SERVER_URL + "/cardno/member-details/", params={"card_number": card_number})
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



def send_event_creation_email(business_email, business_name, event_title, event_date, event_venue):
    subject = f"New Event Created: {event_title}"
    body = f"""
Dear {business_name},

Your event titled "{event_title}" has been successfully created.

📅 Date: {event_date}
📍 Venue: {event_venue}

You can view or manage your event in the JSJ Dashboard.

For any queries, feel free to contact us:
📧 contact@jsjcard.com
📞 +91 99370 02897

Best Regards,  
JSJ Card Team
    """

    api_url = "https://jfe0fa6le4.execute-api.ap-south-1.amazonaws.com/Version1/BulkEmail/"
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)

    try:
        response = requests.get(
            f"{api_url}?sender=contact@jsjcard.com&recipient={business_email}&subject={encoded_subject}&body={encoded_body}"
        )

        if response.status_code == 200:
            print(f"✅ Email sent to: {business_email}")
            return True
        else:
            print(f"❌ Failed to send email. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
    
    
    
def send_bulk_email(member_email, subject, body):
    """
    Send an email using the external BulkEmail API.
    """
    api_url = "https://jfe0fa6le4.execute-api.ap-south-1.amazonaws.com/Version1/BulkEmail/"

    # URL encode subject and body to be passed as query parameters
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)

    try:
        # Send a GET request to your email API
        response = requests.get(
            f"{api_url}?sender=contact@jsjcard.com&recipient={member_email}&subject={encoded_subject}&body={encoded_body}"
        )

        # Check if the response status is 200 (successful)
        if response.status_code == 200:
            print(f"✅ Email sent to: {member_email}")
            return True
        else:
            print(f"❌ Failed to send to {member_email}. Status: {response.status_code}")
            print(f"Response Content: {response.content}")  # For debugging
            return False
    except requests.exceptions.RequestException as e:
        # Log the exception if any error occurs while making the request
        print(f"❌ Error sending to {member_email}: {e}")
        return False