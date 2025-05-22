from django.db import models

# Create your models here.
class FieldCategory(models.Model):
    """Model to store field categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    

class JobProfileField(models.Model):
    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Number"),
        ("email", "Email"),
        ("date", "Date"),
        ("select", "Select"),
        ("checkbox", "Checkbox"),
        ("url", "URL"),
    ]
    category = models.ForeignKey(FieldCategory, on_delete=models.CASCADE, related_name="fields", null=True)
    label = models.CharField(max_length=100)
    field_id = models.CharField(max_length=50, unique=True)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(blank=True, null=True, help_text="Default value (can be empty or null)")
    
    option = models.JSONField(blank=True, null=True, help_text="Options for select or checkbox type fields")

    def __str__(self):
        return self.label

    def to_dict(self):
        """Return field data as dictionary"""
        return {
            "label": self.label,
            "id": self.field_id,
            "type": self.field_type,
            "is_required": self.is_required,
            "placeholder": self.placeholder,
            "value": self.value,
            "option": self.option,
        }