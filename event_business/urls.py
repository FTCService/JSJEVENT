from django.urls import path
from . import views


app_name= "event_business"

urlpatterns = [
  
    path("create/events/", views.BizEventListCreateView.as_view(), name="event-list-create"),
    path("update/events/<int:pk>/", views.BizEventDetailView.as_view(), name="event-detail"),
    path("events/<int:pk>/status/", views.BizEventStatusUpdateView.as_view(), name="event-status"),
    path('api/event-dashboard/', views.EventDashboardAPIView.as_view(), name='event-dashboard'),
    path('registrations/<int:event_id>/list', views.MemberRegistrationListView.as_view(), name='event-registrations-list'),
    path("event-registration/field", views.EventRegistrationFieldsFormattedApi.as_view(), name="event-registration-fields"),
    path('registrations/<int:event_id>/details/<int:cardno>/', views.MemberRegistrationDetailView.as_view(), name='event-registration-details'),
    
    path('attendance/<int:event_id>/list', views.MemberAttendanceList.as_view(), name='event-attendance-list'),
    path('Pending/attendance/<int:event_id>/list', views.MemberPendingAttendanceList.as_view(), name='pending-attendance-list'),
    path('events/<int:event_id>/attendance/', views.EventAttendanceView.as_view(), name='event-attendance'),
    
    path('all/registrations/', views.AllEventAllRegistrations.as_view(), name='all_event_all_registrations'),
    path("create-event-user/", views.EventUserCreateApi.as_view(), name="create-event-user"),
    path('temp-login/<str:token>/', views.TempUserLoginApi.as_view(), name='temp-login'),
]

  
