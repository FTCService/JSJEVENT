from django.urls import path
from . import views


app_name= "event_business"

urlpatterns = [
  
    path("create/events/", views.BizEventListCreateView.as_view(), name="event-list-create"),
    path("update/events/<int:pk>/", views.BizEventDetailView.as_view(), name="event-detail"),
    path("events/<int:pk>/status/", views.BizEventStatusUpdateView.as_view(), name="event-status"),
    path('api/event-dashboard/', views.EventDashboardAPIView.as_view(), name='event-dashboard'),
    
    path("event-registration/field", views.EventRegistrationFieldsFormattedApi.as_view(), name="event-registration-fields"),
    
    path("create-event-user/", views.EventUserCreateApi.as_view(), name="create-event-user"),
    path('temp-login/<str:token>/', views.TempUserLoginApi.as_view(), name='temp-login'),
]

  
