from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import BizEvent, EventRegistration
from .serializers import BizEventSerializer,EventRegistrationSerializer
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .authentication import SSOBusinessTokenAuthentication, TempUserTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from event_admin.models import FieldCategory
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from django.template.loader import render_to_string
import urllib.parse
from helpers.utils import get_business_details_by_id, send_template_email, get_member_details_by_card, get_member_details_by_mobile_number
from . import models
from helpers.temp_access import generate_temp_token, send_temp_login_link
from .serializers import EventUserCreateSerializer, TempUserLoginSerializer,ManageBoothParticipantSerializer
from helpers.pagination import paginate


class BizEventListCreateView(APIView):
    """List all events or create a new one"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: BizEventSerializer(many=True)}
    )
    
    def get(self, request):
        status_filter = request.GET.get('status', None)

        
       
        business = get_business_details_by_id(request.user.business_id)
       
        business_id=business.get("business_id")
        
        if not business_id:
            
            return Response({"message": "Business not found."}, status=status.HTTP_200_OK)

        # Automatically update event status based on current time and end date
        events = BizEvent.objects.filter(BizEventBizId=business_id)

        now = timezone.now()
        for event in events:
            if event.BizEventEndDate < now and event.BizEventStatus == "active":
                event.BizEventStatus = "inactive"
                event.save()

        # Now re-fetch after update
        events = BizEvent.objects.filter(BizEventBizId=business_id)

        if status_filter:
            events = events.filter(BizEventStatus=status_filter)

        events = events.order_by('-id')
        serializer = BizEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        request_body=BizEventSerializer,
        responses={201: BizEventSerializer()},
    )
    def post(self, request):
        """Create an event and associate it with the user's business"""

        serializer = BizEventSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            event = serializer.save()

            business = get_business_details_by_id(request.user.business_id)
            business_id = business.get("business_id")
            email = business.get("email")
            business_name = business.get("business_name")

            # send_event_creation_email(
            #     business_email=email,
            #     business_name=business_name,
            #     event_title=event.BizEventTitle,
            #     event_date=event.BizEventStartDate,
            #     event_venue=event.BizEventLocation
            # )

            return Response(
                {"success": True, "message": "Event created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"success": False, "error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )





class BizEventDetailView(APIView):
    """Retrieve, update, or delete an event by ID"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: BizEventSerializer()}
    )
    def get(self, request, pk):
        event = get_object_or_404(BizEvent, pk=pk)
        serializer = BizEventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        request_body=BizEventSerializer,
        responses={200: BizEventSerializer()},
    )
    def put(self, request, pk):
        event = get_object_or_404(BizEvent, pk=pk)
        serializer = BizEventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        responses={204: "Event deleted successfully"}
    )
    def delete(self, request, pk):
        event = get_object_or_404(BizEvent, pk=pk)
        event.delete()
        return Response({"message": "Event deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class BizEventStatusUpdateView(APIView):
    """Activate or Deactivate an event"""

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "BizEventStatus": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["Active", "Inactive"],
                    description="Update event status to 'Active' or 'Inactive'",
                )
            },
            required=["BizEventStatus"]
        ),
        responses={200: openapi.Response("Event status updated successfully")}
    )
    def patch(self, request, pk):
        """Update the event status"""
        event = get_object_or_404(BizEvent, pk=pk)
        new_status = request.data.get("BizEventStatus")

        if new_status not in ["Active", "Inactive"]:
            return Response(
                {"success": False, "error": "Invalid status. Use 'Active' or 'Inactive'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.BizEventStatus = new_status
        event.save()

        return Response(
            {"success": True, "message": f"Event status updated to {new_status}"},
            status=status.HTTP_200_OK
        )





class EventRegistrationFieldsFormattedApi(APIView):
    """API to get all categories with their fields formatted as key-value pairs."""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Define the response schema for Swagger
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="List of all categories with their fields formatted as key-value pairs.",
                examples={
                    "application/json": {
                        "BasicInformation": {
                            "first_name": {
                                "label": "First Name",
                                "field_id": "first_name",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your first name",
                                
                                "value": ""
                            },
                            "last_name": {
                                "label": "Last Name",
                                "field_id": "last_name",
                                "field_type": "text",
                                "is_required": False,
                                "placeholder": "Enter your last name",
                                "value": ""
                            }
                        },
                        "workexperience": {},
                        "skills": {
                            "python": {
                                "label": "Python",
                                "field_id": "python",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your Python skills",
                                "value": ""
                            }
                        }
                    }
                },
            )
        },
        
    )
    def get(self, request):
        # Get all categories and related fields
        categories = FieldCategory.objects.prefetch_related("fields").all()

        # Define the response structure
        response_data = {}

        # Loop through each category and prepare data
        for category in categories:
            category_fields = {}

            # Loop through fields of each category
            for field in category.fields.all():
                # Prepare field details
                field_data = {
                    "label": field.label,
                    "field_id": field.field_id,
                    "field_type": field.field_type,
                    "is_required": field.is_required,
                    "placeholder": field.placeholder,
                    "option": field.option,
                    "value": [] if field.field_type == "checkbox" else None,
                }

                # Add field data with field_id as key
                category_fields[field.field_id] = field_data

            # Add category fields to the response
            response_data[category.name] = category_fields

        return Response(response_data, status=status.HTTP_200_OK)
    
    


class MemberRegistrationListView(APIView):
    """Retrieve all registrations for a specific event"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Fetch all registrations for a given event (paginated)",
        responses={200: EventRegistrationSerializer(many=True)},
        tags=["Event Registrations"]
    )
    def get(self, request, event_id):
        """Fetch all registrations for a given event_id"""
        event = get_object_or_404(BizEvent, id=event_id)
        registrations = EventRegistration.objects.filter(Event=event).order_by("-created_at")

        if not registrations.exists():
            return Response(
                {"success": False, "message": "No registrations found for this event"},
                status=status.HTTP_200_OK
            )

        # Paginate registrations
        page, pagination_meta = paginate(
            request,
            registrations,
            data_per_page=int(request.GET.get("page_size", 20))
        )

        serializer = EventRegistrationSerializer(page, many=True)

        total_count = registrations.count()
        attended_count = registrations.filter(EventAttended=True).count()
        pending_count = total_count - attended_count

        return Response({
            "status": 200,
            "message": "Registrations fetched successfully",
            "data": serializer.data,
            "pagination_meta_data": pagination_meta,
            "total_registrations": total_count,
            "attended": attended_count,
            "pending_attendance": pending_count
        }, status=status.HTTP_200_OK)
        
        
        
        
class MemberAttendanceList(APIView):
    """Retrieve all Member Attendance List for a specific event"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Fetch all attended registrations for a given event (paginated)",
        responses={200: "Paginated Event Registration List"},
        tags=["Event Attendance"]
    )
    def get(self, request, event_id):
        """Fetch all attended registrations for a given event_id"""
        event = get_object_or_404(BizEvent, id=event_id)
        registrations = EventRegistration.objects.filter(Event=event, EventAttended=True).order_by("-created_at")

        if not registrations.exists():
            return Response(
                {"success": False, "message": "No attended registrations found for this event"},
                status=status.HTTP_200_OK
            )

        # Pagination
        page, pagination_meta = paginate(
            request,
            registrations,
            data_per_page=int(request.GET.get("page_size", 20))
        )

        serializer = EventRegistrationSerializer(page, many=True)

        return Response({
            "status": 200,
            "message": "Event attended registrations fetched successfully",
            "data": serializer.data,
            "pagination_meta_data": pagination_meta,
            "total_attended": registrations.count()
        }, status=status.HTTP_200_OK)
        
        
        
        
class MemberPendingAttendanceList(APIView):
    """Retrieve all Member pending Attendance List for a specific event"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Fetch all pending attendance registrations for a given event (paginated)",
        responses={200: "Paginated Event Registration List"},
        tags=["Event Attendance"]
    )
    def get(self, request, event_id):
        """Fetch all pending attendance registrations for a given event_id"""
        event = get_object_or_404(BizEvent, id=event_id)
        registrations = EventRegistration.objects.filter(Event=event, EventAttended=False).order_by("-created_at")

        if not registrations.exists():
            return Response(
                {"success": False, "message": "No pending registrations found for this event"},
                status=status.HTTP_200_OK
            )

        # Pagination
        page, pagination_meta = paginate(
            request,
            registrations,
            data_per_page=int(request.GET.get("page_size", 20))
        )

        serializer = EventRegistrationSerializer(page, many=True)

        return Response({
            "status": 200,
            "message": "Event pending attendance fetched successfully",
            "data": serializer.data,
            "pagination_meta_data": pagination_meta,
            "total_pending": registrations.count()
        }, status=status.HTTP_200_OK)
        
        
class MemberRegistrationDetailView(APIView):
    """Retrieve event registration details by event ID and member card number"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: EventRegistrationSerializer(many=True)},
    )
    def get(self, request, event_id, cardno):
        """Fetch event registration details by event ID and card number"""
        # try:
        registrations = EventRegistration.objects.filter(Event_id=event_id, EventMbrCard=cardno)
        
        if not registrations.exists():
            return Response(
                {"success": False, "message": "No registrations found"},
                status=status.HTTP_200_OK
            )

        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )
    
        # except Exception as e:
        #     return Response(
        #         {"success": False, "error": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )




class EventRegistrationView(APIView):
    """Allows members to register for an event"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=EventRegistrationSerializer,
        responses={201: EventRegistrationSerializer()},
    )
    def post(self, request, event_id):
        """Register a member for an event"""
        try:
            event = BizEvent.objects.get(id=event_id)
        except BizEvent.DoesNotExist:
            return Response({"success": False, "error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            member = Member.objects.get(mbrcardno=request.user.mbrcardno)
        except Member.DoesNotExist:
            return Response(
                {"success": False, "error": "Member with this card number not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if EventRegistration.objects.filter(Event=event, EventMbrCard=member).exists():
            return Response(
                {"success": False, "message": "Member already registered for this event","EventRegistered":True },
                status=status.HTTP_200_OK
            )

        registration_data = request.data
        print(registration_data,"=========================")

        basic_information = registration_data.get("basicInformation", {})
        career_objectives = registration_data.get("CareerObjectivesPreferences", {})
        education_details = registration_data.get("EducationDetails", {})
        work_experience = registration_data.get("WorkExperience", {})
        skills_competencies = registration_data.get("SkillsCompetencies", {})
        achievements_extracurricular = registration_data.get("AchievementsExtracurricular", {})
        other_details = registration_data.get("OtherDetails", {})

        event_registration_data = {
            "BasicInformation": basic_information,
            "CareerObjectivesPreferences": career_objectives,
            "EducationDetails": education_details,
            "WorkExperience": work_experience,
            "SkillsCompetencies": skills_competencies,
            "AchievementsExtracurricular": achievements_extracurricular,
            "OtherDetails": other_details,
        }

        registration = EventRegistration.objects.create(
            Event=event,
            EventMbrCard=member,
            BasicInformation=basic_information,
            CareerObjectivesPreferences=career_objectives,
            EducationDetails=education_details,
            WorkExperience=work_experience,
            SkillsCompetencies=skills_competencies,
            AchievementsExtracurricular=achievements_extracurricular,
            OtherDetails=other_details,
            EventRegistrationData=event_registration_data,
            EventRegistered=True
        )
        
        JobProfile.objects.update_or_create(
            MbrCardNo=member,
            defaults={
                "BasicInformation": basic_information,
                "CareerObjectivesPreferences": career_objectives,
                "EducationDetails": education_details,
                "WorkExperience": work_experience,
                "SkillsCompetencies": skills_competencies,
                "AchievementsExtracurricular": achievements_extracurricular,
                "OtherDetails": other_details,
            }
        )
        
        # Extract email and full name from nested BasicInformation
        email_info = basic_information.get("email", {}) or basic_information.get("email", {})
        member_email = email_info.get("value", member.email)

        name_info = basic_information.get("full_name", {}) or basic_information.get("name", {})
        member_name = name_info.get("value", member.full_name)

        if member_email:
            send_event_registration_email(
                member_email=member_email,
                member_name=member_name,
                event_title=event.BizEventTitle,
                event_date=event.BizEventStartDate,
                event_venue=event.BizEventLocation
            )
            
        serializer = EventRegistrationSerializer(registration)
        return Response(
            {"EventRegistered":True,"success": True, "message": "Registration successful", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )



class EventAttendanceView(APIView):
    """Allows event organizers to mark user attendance"""
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["mbrcardno", "registration_data"],
            properties={
                "mbrcardno": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the Member"),
            },
        ),
        responses={201: EventRegistrationSerializer()}
    )
    def post(self, request, event_id):
        mbrcardno = request.data.get("mbrcardno")

        # Validate member card number
        
        member_data = get_member_details_by_card(mbrcardno)
        card_number = member_data.get("mbrcardno")
        if not card_number:
            return Response({"success": False, "message": "Member not found"},
                            status=status.HTTP_200_OK)

        # Check if the member is registered for the event
        try:
            registration = EventRegistration.objects.get(Event_id=event_id, EventMbrCard=card_number)
        except EventRegistration.DoesNotExist:
            return Response({"success": False, "message": "User not registered for this event"},
                            status=status.HTTP_200_OK)

        # Check if the user is already marked as attended
        if registration.EventAttended:
            return Response({"success": False, "message": "User already marked as attended"},
                            status=status.HTTP_200_OK)

        # Mark user as attended
        registration.EventAttended = True
        registration.save()

        return Response({"success": True, "message": "Attendance marked successfully"},
                        status=status.HTTP_200_OK)




class EventDashboardAPIView(APIView):
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get dashboard metrics for the authenticated business user",
        responses={
            200: openapi.Response(
                description="Dashboard stats",
                examples={
                    "application/json": {
                        "total_events": 5,
                        "total_registrations": 125,
                        "total_attendance": 87,
                        "time_series": [
                            {"x": "2025-04-04", "registrations": 10, "attendances": 5},
                            {"x": "2025-04-05", "registrations": 20, "attendances": 12},
                            # ...
                        ]
                    }
                }
            )
        }
    )
    def get(self, request):
        user_business = request.user.business_id 

        total_events = BizEvent.objects.filter(BizEventBizId=user_business).count()

        total_registrations = EventRegistration.objects.filter(Event__BizEventBizId=user_business).count()

        total_attendance = EventRegistration.objects.filter(
            Event__BizEventBizId=user_business,
            EventAttended=True
        ).count()

        time_series_data = []
        for i in range(7):
            day = now().date() - timedelta(days=6 - i)
            registrations = EventRegistration.objects.filter(
                Event__BizEventBizId=user_business,
                created_at__date=day
            ).count()

            attendance = EventRegistration.objects.filter(
                Event__BizEventBizId=user_business,
                EventAttended=True,
                created_at__date=day
            ).count()

            time_series_data.append({
                "x": day.strftime("%Y-%m-%d"),
                "registrations": registrations,
                "attendances": attendance
            })

        return Response({
            "total_events": total_events,
            "total_registrations": total_registrations,
            "total_attendance": total_attendance,
            "time_series": time_series_data
        })
        
        

class AllEventAllRegistrations(APIView):
    """
    API to retrieve all event registrations across all events with pagination.
    """
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all event registrations across all events (paginated).",
        responses={200: EventRegistrationSerializer(many=True)},
        tags=["Event Registrations"]
    )
    def get(self, request):
        registrations = EventRegistration.objects.all().order_by("-created_at")

        # Use custom paginate helper
        page, pagination_meta = paginate(
            request,
            registrations,
            data_per_page=int(request.GET.get("page_size", 20))
        )

        serialized_data = EventRegistrationSerializer(page, many=True).data

        return Response({
            "status": 200,
            "data": serialized_data,
            "pagination_meta_data": pagination_meta
        }, status=status.HTTP_200_OK)
        
        
class SendBulkEventEmail(APIView):
    """
    API to send bulk emails to a provided list of members.
    Email and name are taken from request payload (frontend input format).
    """
    authentication_classes = [SSOBusinessTokenAuthentication]  # Add your CustomTokenAuthentication if required
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Send bulk emails to recipients using a template.",
        manual_parameters=[
            openapi.Parameter(
                'event_id',
                openapi.IN_PATH,
                description="ID of the event",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["subject", "body", "recipients"],
            properties={
                "subject": openapi.Schema(type=openapi.TYPE_STRING, description="Email Subject"),
                "body": openapi.Schema(type=openapi.TYPE_STRING, description="Email Body (can be HTML)"),
                "recipients": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                            "email": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                        }
                    ),
                    description="List of recipients with name and email"
                ),
            }
        ),
        responses={200: openapi.Response(description="Result of sending emails")}
    )
    
    def post(self, request):
        subject = request.data.get("subject")
        body = request.data.get("body")
        recipients = request.data.get("recipients")

        # Ensure required fields are present
        if not subject or not body or not recipients:
            return Response(
                {"success": False, "message": "Subject, body, and recipients are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        success_emails = []
        failed_emails = []

        # Process each recipient
        for member in recipients:
            member_name = member.get("name")
            member_email = member.get("email")
            if member_email:
                # Render email template with context
                context = {
                    "name": member_name,   # Name of recipient
                    "content": body        # Dynamic content you want to include in the email
                }
                html_content = render_to_string("event/email/bulk_email_template.html", context)

                # Send the email using the custom send_email function
                success = send_bulk_email(member_email, subject, html_content)
                if success:
                    success_emails.append(member_email)
                else:
                    failed_emails.append({"email": member_email, "reason": "Failed to send via API"})

        return Response({
            "success": True,
            "message": "Emails processed.",
            "emails_sent": success_emails,
            "emails_failed": failed_emails
        }, status=status.HTTP_200_OK)




class EventUserCreateApi(APIView):
    authentication_classes = [SSOBusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        business_id = request.user.business_id
        
        # ✅ Read query parameter: defaults to 'booth' if not provided
        user_type = request.query_params.get('usertype', 'booth').lower()

        # ✅ Ensure only allowed values
        if user_type not in ['booth', 'volunteer']:
            return Response(
                {"error": "Invalid usertype. Allowed values are 'booth' or 'volunteer'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Get all events for the current business
        events = BizEvent.objects.filter(BizEventBizId=business_id , id=event_id)

        # ✅ Filter TempUser by events and requested user_type
        booths_or_volunteers = models.TempUser.objects.filter(
            event__in=events,
            user_type=user_type
        ).order_by('id')

        # ✅ Prepare response
        data = [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "mobile_number": u.mobile_number,
                "event_id": u.event.id,
                "event_name": u.event.BizEventTitle
            }
            for u in booths_or_volunteers
        ]

        return Response({"data": data}, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        request_body=EventUserCreateSerializer,
        responses={
            201: EventUserCreateSerializer,
            400: 'Bad Request',
        },
        operation_description="Create a temporary event user (booth or volunteer) and generate login URL",
    )
    def post(self, request, event_id):
        serializer = EventUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # Get event object
            try:
                event = BizEvent.objects.get(id=event_id)
            except BizEvent.DoesNotExist:
                return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

            # Prevent duplicate active token users with same email and type
            if models.TempUser.objects.filter(email=data['email'], user_type=data['user_type'], event=event).exists():
                return Response(
                    {"error": f"Temp user with this email and type '{data['user_type']}' already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = generate_temp_token()
            expires_at = timezone.now() + timedelta(hours=1)

            temp_user = models.TempUser.objects.create(
                event=event,  # ✅ required field
                full_name=data['full_name'],
                email=data['email'],
                mobile_number=data['mobile_number'],
                user_type=data['user_type'],
                token=token,
                expires_at=expires_at,
            )

            login_url = send_temp_login_link(temp_user)["login_url"]

            email_context = {
                'full_name': temp_user.full_name,
                'email': temp_user.email,
                'mobile_number': temp_user.mobile_number,
                'login_url': login_url,
                'expires_at': temp_user.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            }

            send_template_email(
                subject="Welcome to JSJCard!",
                template_name="email_template/event_user.html",
                context=email_context,
                recipient_list=[temp_user.email]
            )

            return Response({"login_url": login_url, "user_type": temp_user.user_type}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TempUserLoginApi(APIView):

    def get(self, request, token, event_id, user_type):
        try:
            temp_user = models.TempUser.objects.get(
                token=token, 
                event_id=event_id, 
                user_type=user_type
            )
        except models.TempUser.DoesNotExist:
            return Response({"error": "Invalid token or user type"}, status=status.HTTP_400_BAD_REQUEST)

        if temp_user.expires_at < timezone.now():
            return Response({"error": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "full_name": temp_user.full_name,
            "email": temp_user.email,
            "token": temp_user.token,
            "user_type": temp_user.user_type,
            "token_valid": True
        }, status=status.HTTP_200_OK)

    def post(self, request, token, event_id, user_type):
        serializer = TempUserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        try:
            temp_user = models.TempUser.objects.get(
                token=token, 
                event_id=event_id, 
                user_type=user_type
            )
        except models.TempUser.DoesNotExist:
            return Response({"error": "Invalid token or user type"}, status=status.HTTP_400_BAD_REQUEST)

        # if temp_user.expires_at < timezone.now():
        #     return Response({"error": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

        if temp_user.email.lower() != email.lower():
            return Response({"error": "Email does not match"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Login successful",
            "user": {
                "full_name": temp_user.full_name,
                "email": temp_user.email,
                "mobile_number": temp_user.mobile_number,
                "user_type": temp_user.user_type,
            },
            "token": temp_user.token,
            "expires_at": temp_user.expires_at,
        }, status=status.HTTP_200_OK)

        

class MemberParticipantBooth(APIView):
    """
    API to manage and retrieve participant details in the event booth,
    using card number (16 digits) or mobile number (10 digits).
    """

    authentication_classes = [TempUserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('card_no', openapi.IN_QUERY, description="Card number (16 digits) or Mobile number (10 digits)", type=openapi.TYPE_STRING),
        ],
        responses={200: "Participant details"},
        tags=[" Booth "]
    )
    def get(self, request, event_id):
        card_no = request.GET.get("card_no")

        if not card_no:
            return Response(
                {"error": "Please provide a card number or mobile number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Decide whether it's a card number or mobile number
        mbrcardno = None
        if len(card_no) == 16 and card_no.isdigit():
            # Directly use as card number
            mbrcardno = card_no
        elif len(card_no) == 10 and card_no.isdigit():
            # Lookup by mobile number
            member_data = get_member_details_by_mobile_number(card_no)
            mbrcardno = member_data.get("mbrcardno") if member_data else None
        else:
            return Response(
                {"error": "Invalid input. Provide a valid 16-digit card number or 10-digit mobile number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not mbrcardno:
            return Response(
                {"success": False, "message": "Member not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Check if booth is assigned to user
        try:
            booth = models.TempUser.objects.get(id=request.user.id, event_id=event_id)
        except models.TempUser.DoesNotExist:
            return Response(
                {"error": "Booth not assigned to this user for the event."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ Find participant in EventRegistration
        participant = EventRegistration.objects.filter(
            EventMbrCard=mbrcardno,
            Event_id=event_id
        ).first()

        if not participant:
            return Response(
                {"success": False, "message": "The member is not registered for this event."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Build response
        participant_info = {
            "participant_id": participant.id,
            "card_no": participant.EventMbrCard,
            "event_id": participant.Event.id,
            "event_name": getattr(participant.Event, "BizEventTitle", None),
            "BasicInformation": participant.BasicInformation,
            "CareerObjectivesPreferences": participant.CareerObjectivesPreferences,
            "EducationDetails": participant.EducationDetails,
            "WorkExperience": participant.WorkExperience,
            "SkillsCompetencies": participant.SkillsCompetencies,
            "AchievementsExtracurricular": participant.AchievementsExtracurricular,
            "OtherDetails": participant.OtherDetails,
            "EventAttended": participant.EventAttended,
            "EventRegistered": participant.EventRegistered,
            "created_at": participant.created_at,
        }

        return Response(participant_info, status=status.HTTP_200_OK)
    @swagger_auto_schema(
    request_body=ManageBoothParticipantSerializer,
    tags=[" Booth "]
    )
    def post(self, request, event_id):
        """
        Add or update participant information in a booth for a specific event 
        using card number (16 digits) or mobile number (10 digits).
        Save full participant response with timestamp.
        """
        serializer = ManageBoothParticipantSerializer(data=request.data)
        if serializer.is_valid():
            card_no = serializer.validated_data["card_no"]
            status_value = serializer.validated_data["status"]
            comment = serializer.validated_data["comment"]

            # ✅ Check booth assignment
            try:
                booth = models.TempUser.objects.get(id=request.user.id, event_id=event_id)
            except models.TempUser.DoesNotExist:
                return Response(
                    {"error": "Booth not assigned to this user for the event."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # ✅ Decide card_no vs mobile_no
            mbrcardno = None
            if len(card_no) == 16 and card_no.isdigit():
                mbrcardno = card_no
            elif len(card_no) == 10 and card_no.isdigit():
                member_data = get_member_details_by_mobile_number(card_no)
                mbrcardno = member_data.get("mbrcardno") if member_data else None
            else:
                return Response(
                    {"error": "Invalid input. Provide a valid 16-digit card number or 10-digit mobile number."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not mbrcardno:
                return Response(
                    {"error": "Member not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # ✅ Fetch participant
            participant = EventRegistration.objects.filter(
                EventMbrCard=mbrcardno,
                Event_id=event_id
            ).first()

            if not participant:
                return Response(
                    {"error": "Participant not found for this event."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # ✅ Prepare data to save
            entry = {
                "card_no": mbrcardno,
                "status": status_value,
                "comment": comment,
                "timestamp": datetime.now().isoformat(),
                "BasicInformation": participant.BasicInformation,
                "CareerObjectivesPreferences": participant.CareerObjectivesPreferences,
                "EducationDetails": participant.EducationDetails,
                "WorkExperience": participant.WorkExperience,
                "SkillsCompetencies": participant.SkillsCompetencies,
                "AchievementsExtracurricular": participant.AchievementsExtracurricular,
                "OtherDetails": participant.OtherDetails,
            }

            if booth.boothintraction is None:
                booth.boothintraction = {}

            # ✅ Save by participant ID as key
            booth.boothintraction[str(participant.id)] = entry
            booth.save()

            return Response(
                {"message": "Participant details updated and saved successfully."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VolunteerTakeAttendance(APIView):
    """
    Allows volunteers to mark user attendance and store their marked members with timestamp.
    """
    authentication_classes = [TempUserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["mbrcardno"],
            properties={
                "mbrcardno": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the Member"),
            },
        ),
        responses={200: openapi.Response(description="Attendance response")},
        tags=["Volunteer"]
    )
    def post(self, request, event_id):
        mbrcardno = request.data.get("mbrcardno")
        volunteer = request.user # this is the TempUser instance

        # Check if the volunteer is assigned to the event
        if volunteer.event_id != int(event_id):
            return Response(
                {"success": False, "message": "You are not assigned to this event"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate Member
        member = get_member_details_by_card(mbrcardno)
        mbrcardno = member.get("mbrcardno")

        # Validate Registration
        try:
            registration = EventRegistration.objects.get(Event_id=event_id, EventMbrCard=mbrcardno)
        except EventRegistration.DoesNotExist:
            return Response(
                {"success": False, "message": "User not registered for this event"},
                status=status.HTTP_200_OK
            )

        if registration.EventAttended:
            return Response(
                {"success": False, "message": "User already marked as attended"},
                status=status.HTTP_200_OK
            )

        # Mark attendance
        registration.EventAttended = True
        registration.save()

        # Append to AttendMember JSON
        timestamp = now().isoformat()

        attend_data = volunteer.boothintraction.get(str(event_id), [])
        # Prevent duplicate entry
        if any(entry["cardno"] == mbrcardno for entry in attend_data):
            return Response(
                {"success": False, "message": "Member already recorded by volunteer"},
                status=status.HTTP_200_OK
            )

        attend_data.append({"cardno": mbrcardno, "timestamp": timestamp})
        volunteer.boothintraction[str(event_id)] = attend_data
        volunteer.save()

        return Response({
            "success": True,
            "message": "Attendance marked successfully",
            "cardno": mbrcardno,
            "marked_at": timestamp,
            "total_attended_by_volunteer": len(attend_data)
        }, status=status.HTTP_200_OK)




