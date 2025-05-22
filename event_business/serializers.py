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



