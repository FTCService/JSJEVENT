from rest_framework import serializers
from .models import BizEvent,EventRegistration



class BizEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BizEvent
        fields = '__all__'
        extra_kwargs = {
            "BizEventBizId": {"required": False, "read_only": True}
        }

    def create(self, validated_data):
        """Set BizEventBizId automatically before saving"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'business_id'):
            raise serializers.ValidationError({"BizEventBizId": "User must be associated with a business."})

        validated_data["BizEventBizId"] = request.user.business_id
        return super().create(validated_data)



class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = "__all__"



class EventUserCreateSerializer(serializers.Serializer):
    BoothEvent = serializers.IntegerField()
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    mobile_number = serializers.CharField(max_length=15)
    user_type = serializers.ChoiceField(choices=[('booth', 'Booth'), ('volunteer', 'Volunteer')])
    
    

class TempUserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    

class ManageBoothParticipantSerializer(serializers.Serializer):
    card_no = serializers.CharField(max_length=255)
    status = serializers.ChoiceField(choices=['hired', 'shortlisted', 'rejected'])
    comment = serializers.CharField(max_length=1024, required=False)