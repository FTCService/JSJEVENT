from django.urls import path
from . import views


app_name= "event_admin"

urlpatterns = [
  
   path("category/", views.CategoryListCreateApi.as_view(), name="category_list_create"),
   path("category/<int:category_id>/", views.CategoryDetailApi.as_view(), name="category_detail"),
   path('category/profile-fields/', views.JobProfileFieldListByCategory.as_view(), name='job-profile-fields'),
   
   
   path("fields/", views.JobProfileFieldListApi.as_view(), name="list-fields"),
   path("fields/create/", views.JobProfileFieldCreateApi.as_view(), name="create-field"),
   path("fields/<int:id>/", views.JobProfileFieldDetailApi.as_view(), name="field-detail"),
  
  
]

  
