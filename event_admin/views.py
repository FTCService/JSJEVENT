from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from . import serializers
from .models import JobProfileField, FieldCategory
from django.shortcuts import get_object_or_404
from .authentication import SSOUserTokenAuthentication
from collections import defaultdict


class CategoryListCreateApi(APIView):
    """List and Create Categories"""
    authentication_classes = [SSOUserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all categories.",
        responses={200: serializers.CategorySerializer(many=True)},
    )
    def get(self, request):
        categories = FieldCategory.objects.all()
        serializer = serializers.CategorySerializer(categories, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.CategorySerializer,
        operation_description="Create a new category.",
        responses={201: serializers.CategorySerializer()},
    )
    def post(self, request):
        # Check for duplicate category name
        if FieldCategory.objects.filter(name=request.data.get('name')).exists():
            return Response(
                {"error": "Category with this name already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = serializers.CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Category created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailApi(APIView):
    """Retrieve, Update, and Delete a Category"""
    authentication_classes = [SSOUserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, category_id):
        try:
            return FieldCategory.objects.get(id=category_id)
        except FieldCategory.DoesNotExist:
            raise NotFound("Category not found")

    @swagger_auto_schema(
        operation_description="Retrieve a specific category by ID.",
        responses={200: serializers.CategorySerializer()},
    )
    def get(self, request, category_id):
        category = self.get_object(category_id)
        serializer = serializers.CategorySerializer(category)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.CategorySerializer,
        operation_description="Update a category by ID.",
        responses={200: serializers.CategorySerializer()},
    )
    def put(self, request, category_id):
        category = self.get_object(category_id)
        serializer = serializers.CategorySerializer(
            category, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Category updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a category by ID.",
        responses={200: "Category deleted successfully"},
    )
    def delete(self, request, category_id):
        category = self.get_object(category_id)
        category.delete()
        return Response(
            {"message": "Category deleted successfully"}, status=status.HTTP_200_OK
        )
        
        
        
        
class JobProfileFieldListByCategory(APIView):
    authentication_classes = [SSOUserTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get list of job profile fields for a specific category (grouped by category name)",
        manual_parameters=[
            openapi.Parameter(
                'category_id',
                openapi.IN_QUERY,
                description="ID of the category",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Fields grouped by category name",
                examples={
                    "application/json": {
                        "status": True,
                        "basicInformation": [
                            {
                                "id": 6,
                                "option": [],
                                "label": "full name",
                                "field_id": "full_name",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your Full Name",
                                "value": ""
                            },
                            {
                                "id": 7,
                                "option": [],
                                "label": "gender",
                                "field_id": "gender",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your gender",
                                "value": ""
                            }
                        ]
                    }
                }
            )
        }
    )
    def get(self, request):
        category_id = request.query_params.get("category_id")
        if not category_id:
            return Response({
                "status": False,
                "message": "category_id is required"
            }, status=200)

        fields = JobProfileField.objects.filter(category_id=category_id)
        if not fields.exists():
            return Response({
                "status": False,
                "message": "No fields found for this category"
            }, status=200)

        serialized_fields = serializers.JobProfileFieldSerializer(fields, many=True).data
        for item in serialized_fields:
            item.pop("category", None)
            item.pop("category_name", None)

        return Response({
            "status": True,
            "data": serialized_fields
        })

    @swagger_auto_schema(
        operation_description="Create or update a job profile field. Pass 'id' to update, omit 'id' to create.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'label': openapi.Schema(type=openapi.TYPE_STRING, description='Label'),
                'field_id': openapi.Schema(type=openapi.TYPE_STRING, description='Field ID'),
                'field_type': openapi.Schema(type=openapi.TYPE_STRING, description='Field Type'),
                'placeholder': openapi.Schema(type=openapi.TYPE_STRING, description='Placeholder text'),
                'is_required': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is required'),
                'value': openapi.Schema(type=openapi.TYPE_STRING, description='Default value'),
                'option': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='Options (for select fields)'
                )
            }
        ),
        responses={
            200: openapi.Response(description="Field created or updated successfully")
        }
    )
    def post(self, request):
        data = request.data

        # Check if the input is a list (bulk) or dict (single)
        fields_data = data if isinstance(data, list) else [data]

        response_fields = []

        for field_data in fields_data:
            field_id_value = field_data.get("field_id")
            print("field_id_value",field_id_value,"----------")
            if field_id_value:
                try:
                    field = JobProfileField.objects.get(field_id=field_id_value)
                    serializer = serializers.JobProfileFieldSerializer(field, data=field_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        response_fields.append({
                            "status": True,
                            "message": f"Field '{field_id_value}' updated successfully",
                            "field": serializer.data
                        })
                        continue
                    else:
                        response_fields.append({
                            "status": False,
                            "message": f"Validation failed for '{field_id_value}'",
                            "errors": serializer.errors
                        })
                        continue
                except JobProfileField.DoesNotExist:
                    pass  # Not found, will create below

            # Create new field if not found
            serializer = serializers.JobProfileFieldSerializer(data=field_data)
            if serializer.is_valid():
                serializer.save()
                response_fields.append({
                    "status": True,
                    "message": f"Field '{field_data.get('field_id')}' created successfully",
                    "field": serializer.data
                })
            else:
                response_fields.append({
                    "status": False,
                    "message": f"Validation failed for '{field_data.get('field_id')}'",
                    "errors": serializer.errors
                })

        return Response({
            "status": True,
            "results": response_fields
        }, status=status.HTTP_200_OK)
        
        
        
class JobProfileFieldListApi(APIView):
    """API to list all dynamic fields grouped by category."""
    authentication_classes = [SSOUserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all dynamic fields grouped by category.",
        responses={200: "Grouped dynamic fields by category"}
    )
    def get(self, request):
        fields = JobProfileField.objects.all()
        serializer = serializers.JobProfileFieldSerializer(fields, many=True)

        # Grouping logic
        grouped_fields = defaultdict(list)
        for field in serializer.data:
            key = (field["category_name"], field["category"])
            grouped_fields[key].append({
                "label": field["label"],
                "field_id": field["field_id"],
                "field_type": field["field_type"],
                "is_required": field["is_required"],
                "placeholder": field["placeholder"],
                "value": field.get("value", ""),
                "option": field.get("option", []) if field["field_type"] == "select" else []
            })

        # Prepare final structured response
        response_data = []
        for (category_name, category_id), fields_list in grouped_fields.items():
            response_data.append({
                "category_name": category_name,
                "category": category_id,
                "fields": fields_list
            })

        return Response(response_data, status=status.HTTP_200_OK)


class JobProfileFieldDetailApi(APIView):
    """API to retrieve, update or delete a specific field."""
    authentication_classes = [SSOUserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        try:
            return JobProfileField.objects.get(id=id)
        except JobProfileField.DoesNotExist:
            raise NotFound("Field not found")

    @swagger_auto_schema(
        operation_description="Retrieve a specific field by ID.",
        responses={200: serializers.JobProfileFieldSerializer()},
    )
    def get(self, request, id):
        field = self.get_object(id)
        serializer = serializers.JobProfileFieldSerializer(field)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.JobProfileFieldSerializer,
        operation_description="Update a field by ID.",
        responses={200: serializers.JobProfileFieldSerializer()},
    )
    def put(self, request, id):
        field = self.get_object(id)
        serializer = serializers.JobProfileFieldSerializer(
            field, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Field updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @swagger_auto_schema(
        operation_description="Delete a field by ID.",
        responses={200: "Field deleted successfully"},
    )
    def delete(self, request, id):
        field = self.get_object(id)
        field.delete()
        return Response(
            {"message": "Field deleted successfully"}, status=status.HTTP_200_OK
        )
         
         
class JobProfileFieldCreateApi(APIView):
    """API to create a new dynamic field."""
    authentication_classes = [SSOUserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.JobProfileFieldSerializer,
        operation_description="Create a new dynamic field.",
        responses={201: serializers.JobProfileFieldSerializer()},
    )
    def post(self, request):
        serializer = serializers.JobProfileFieldSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Field created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   