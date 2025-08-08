from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from event_business.models import BizEvent, EventRegistration
from .serializers import  MbrEventSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .authentication import SSOMemberTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from event_admin.models import FieldCategory
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from helpers.utils import get_member_details_by_card
from django.shortcuts import get_object_or_404


class MbrEventListView(APIView):
    """List events filtered by member address and registration status"""
    authentication_classes = [SSOMemberTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: MbrEventSerializer(many=True)}
    )
    def get(self, request):
        card_number = request.user.mbrcardno

      
        member_data = get_member_details_by_card(card_number)
       
        if not member_data:
            
            # If member not found, return an error response
            return Response({"error": "Member not found."}, status=status.HTTP_404_NOT_FOUND)
        full_name = member_data.get('full_name')
        email = member_data.get('email')
        card_number = member_data.get('card_number')
       

        registered_event_ids = set(EventRegistration.objects.filter(
            EventMbrCard=card_number
        ).values_list("Event_id", flat=True))

        # Filter events
        events = BizEvent.objects.all()
            
        serializer = MbrEventSerializer(events, many=True)

        # Add EventRegistered flag to each serialized event
        for event_data in serializer.data:
            event_data["EventRegistered"] = int(event_data["id"]) in registered_event_ids

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
class MbrEventDetailView(APIView):
    authentication_classes = [SSOMemberTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: MbrEventSerializer()})
    def get(self, request, event_id):
        event = get_object_or_404(BizEvent, id=event_id)
        serializer = MbrEventSerializer(event)
        event_data = serializer.data

        # Fetch JobProfile of the current user
        
            # Try to get Member instance linked to the logged-in user
        member = request.user.mbrcardno
        if not member:
            return Response({
                "status": False,
                "message": "Invalid user. Member details not found."
            }, status=status.HTTP_200_OK)
            
        # try:
        #     job_profile = JobProfile.objects.get(MbrCardNo=member)
        # except JobProfile.DoesNotExist:
        #     job_profile = None

        # # If job_profile exists, fill registration form values
        # if job_profile:
        #     profile_sections = {
        #         "basicInformation": job_profile.BasicInformation,
        #         "CareerObjectivesPreferences": job_profile.CareerObjectivesPreferences,
        #         "EducationDetails": job_profile.EducationDetails,
        #         "WorkExperience": job_profile.WorkExperience,
        #         "SkillsCompetencies": job_profile.SkillsCompetencies,
        #         "AchievementsExtracurricular": job_profile.AchievementsExtracurricular,
        #         "OtherDetails": job_profile.OtherDetails,
        #     }

            # # Loop through each section and set values
            # reg_form = event_data.get("BizEventRegistrationForm", {})
            # for section_key, section_fields in reg_form.items():
            #     if section_key in profile_sections:
            #         job_section_data = profile_sections[section_key]
            #         for field_key in section_fields:
            #             if field_key in job_section_data and "value" in job_section_data[field_key]:
            #                 reg_form[section_key][field_key]["value"] = job_section_data[field_key]["value"]

            # event_data["BizEventRegistrationForm"] = reg_form

        return Response(event_data, status=status.HTTP_200_OK)
    
    
    
    
class MemberEventRegistrationView(APIView):
    authentication_classes = [SSOMemberTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        member = request.user

        try:
            event = BizEvent.objects.get(id=event_id)
        except BizEvent.DoesNotExist:
            return Response({"success": False, "error": "Event not found"}, status=404)

        try:
            registration = EventRegistration.objects.get(Event=event, EventMbrCard=member)
        except EventRegistration.DoesNotExist:
            return Response({"success": True, "message": "No registration found"}, status=200)

        
        data = {
            "event": registration.Event.BizEventTitle,
            "event_id": registration.Event.id,
            "BasicInformation": extract_label_value(registration.BasicInformation),
            "CareerObjectivesPreferences": extract_label_value(registration.CareerObjectivesPreferences),
            "EducationDetails": extract_label_value(registration.EducationDetails),
            "WorkExperience": extract_label_value(registration.WorkExperience),
            "SkillsCompetencies": extract_label_value(registration.SkillsCompetencies),
            "AchievementsExtracurricular": extract_label_value(registration.AchievementsExtracurricular),
            "OtherDetails": extract_label_value(registration.OtherDetails),
            "EventAttended": registration.EventAttended,
            "registered_at": registration.created_at,
            "EventRegistered":True,
        }

        return Response({"success": True, "message": "Registration data fetched", "data": data}, status=200)
    
def extract_label_value(data):
            return {key: {"label": val.get("label"), "value": val.get("value")} for key, val in data.items()}
        



class MemberSelfAttendanceApi(APIView):
    """
    Allows a member to mark their self-attendance if they are registered for the event.
    """
    
    authentication_classes = [SSOMemberTokenAuthentication]
    permission_classes = [IsAuthenticated]


    @swagger_auto_schema(
        operation_description="Mark self-attendance for a registered event",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['event_id'],
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
            },
        ),
        responses={
            200: openapi.Response(description="All responses (success or failure) return with 200 status code"),
        }
    )
    def post(self, request):
        mbrcardno = request.user.mbrcardno
        event_id = request.data.get("event_id")

        if not mbrcardno or not event_id:
            return Response({
                "status": False,
                "message": "Both mbrcardno and event_id are required"
            }, status=status.HTTP_200_OK)

        
        member = request.user.mbrcardno
        if not member:
            return Response({
                "status": False,
                "message": "Member not found"
            }, status=status.HTTP_200_OK)

        try:
            event = BizEvent.objects.get(id=event_id)
        except BizEvent.DoesNotExist:
            return Response({
                "status": False,
                "message": "Event not found"
            }, status=status.HTTP_200_OK)

        try:
            registration = EventRegistration.objects.get(Event=event, EventMbrCard=member)
        except EventRegistration.DoesNotExist:
            return Response({
                "status": False,
                "message": "Member is not registered for this event"
            }, status=status.HTTP_200_OK)

        if registration.EventAttended:
            return Response({
                "status": False,
                "message": "Attendance already marked"
            }, status=status.HTTP_200_OK)

        registration.EventAttended = True
        registration.save()

        return Response({
            "status": True,
            "message": "Attendance marked successfully"
        }, status=status.HTTP_200_OK)
        
        
        
        
        
class MbrEventRegistrationFormApi(APIView):
    """
    API to fetch all fields from BizEventRegistrationForm for a given event ID.
    """

    def get(self, request, event_id):
        # Fetch the event by ID
        event = get_object_or_404(BizEvent, id=event_id)

        # Get the registration form data
        registration_form_data = event.BizEventRegistrationForm

        # Check if the registration form is not empty
        if not registration_form_data:
            return Response(
                {"status": "error", "message": "No registration form data found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Return the registration form data
        return Response(
            {
                "status": "success",
                "event_id": event.id,
                "BizEventTitle": event.BizEventTitle,
                "BizEventRegistrationForm": registration_form_data,
            },
            status=status.HTTP_200_OK,
        )