from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Interaction, Stage, Application, JobOffer, Assessment


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


class InteractionSerializer(serializers.ModelSerializer):
    """Serializer for Interaction model"""
    application_company_name = serializers.CharField(source='application.company_name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Interaction
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


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
        first_stage = Stage.objects.order_by('order').first()
        if first_stage:
            validated_data['stage'] = first_stage
        
        return super().create(validated_data)


class JobOfferSerializer(serializers.ModelSerializer):
    """Serializer for JobOffer model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    # Make these fields optional in serializer (will be auto-populated from application)
    company_name = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)
    salary_range = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = JobOffer
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')
    
    def validate(self, data):
        """Validate that application is provided and auto-populate fields"""
        if self.instance is None:
            # On create, application is required
            if not data.get('application'):
                raise serializers.ValidationError({
                    'application': 'Application is required to create a job offer.'
                })
            
            # Auto-populate fields from application if not provided
            application = data.get('application')
            if application:
                if not data.get('company_name'):
                    data['company_name'] = application.company_name
                if not data.get('position'):
                    data['position'] = application.position or ''
                if not data.get('salary_range'):
                    data['salary_range'] = application.salary_range or ''
        
        return data
    
    def create(self, validated_data):
        """Create JobOffer with auto-populated fields"""
        return super().create(validated_data)


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    application_company_name = serializers.CharField(source='application.company_name', read_only=True)
    application_position = serializers.CharField(source='application.position', read_only=True)

    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')
