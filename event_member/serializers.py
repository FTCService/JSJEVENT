from rest_framework import serializers
from event_business.models import BizEvent, EventRegistration




        
class MbrEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BizEvent
        fields = '__all__'
        
        
class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = "__all__"