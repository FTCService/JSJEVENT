from django.urls import path

from . import views

app_name = "event_member"


urlpatterns = [
    path("event/list/", views.MbrEventListView.as_view(), name="mbrevent-list"),
    path("event/details/<int:event_id>/", views.MbrEventDetailView.as_view(), name="mbrevent-details"),
    path("my-registrations/<int:event_id>/", views.MemberEventRegistrationView.as_view(), name="member-event-registration"),
    path('<int:event_id>/register/', views.EventRegistrationView.as_view(), name='event-register'),
    
    path('self-attendance/', views.MemberSelfAttendanceApi.as_view(), name='member-self-attendance'),

    path('event/<int:event_id>/registration/', views.MbrEventRegistrationFormApi.as_view(), name='event-registration'),
    
    
    path('event/entry/<int:event_id>/',views.EventEntryPassRegistrationApi.as_view(),name='event-registration-entry'),
]

