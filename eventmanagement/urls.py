from django.contrib import admin
from django.urls import path, include
from helpers import swagger_documentation

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('event/', include('event_business.urls')),
    path('admin/event', include('event_admin.urls')),
    path('member/event/', include('event_member.urls')),
    path('swagger/', swagger_documentation.schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', swagger_documentation.schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]
