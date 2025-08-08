from rest_framework import serializers
from .models import JobProfileField, FieldCategory
import re

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category"""

    class Meta:
        model = FieldCategory
        fields = ["id", "name", "description"]
        
        

class JobProfileFieldSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=FieldCategory.objects.all())
    option = serializers.ListField(child=serializers.CharField(), default=list(), required=False)

    class Meta:
        model = JobProfileField
        fields = "__all__"
        extra_fields = ["category_name"]

    def create(self, validated_data):
        options = validated_data.pop('option', [])
        field = JobProfileField.objects.create(option=options, **validated_data)
        return field

    def update(self, instance, validated_data):
        options = validated_data.pop('option', None)
        if options is not None:
            instance.option = options
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure options are correctly represented from the instance
        data["option"] = instance.option if instance.option is not None else []
        return data