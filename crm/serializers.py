from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, Contact, Interaction, Stage, Application


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    contacts_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')

    def get_contacts_count(self, obj):
        return obj.contacts.count()


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    customer_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Customer.objects.all(), source='customers', required=False
    )

    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class InteractionSerializer(serializers.ModelSerializer):
    """Serializer for Interaction model"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    contact_name = serializers.SerializerMethodField()
    application_company_name = serializers.CharField(source='application.company_name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Interaction
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')

    def get_contact_name(self, obj):
        if obj.contact:
            return f"{obj.contact.first_name} {obj.contact.last_name}"
        return None


class StageSerializer(serializers.ModelSerializer):
    """Serializer for Stage Model"""

    class Meta:
        model = Stage
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Application model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')

    def validate(self, data):
        """Ensure at least one stage exists before creating an application"""
        if self.instance is None and not Stage.objects.exists():
            raise serializers.ValidationError(
                "Cannot create application: no stages exist. Please create a stage first."
            )
        return data

    def create(self, validated_data):
        # If no stage provided, assign to first stage by default
        if validated_data.get('stage') is None:
            first_stage = Stage.objects.order_by('order').first()
            if first_stage:
                validated_data['stage'] = first_stage
        
        return super().create(validated_data)
