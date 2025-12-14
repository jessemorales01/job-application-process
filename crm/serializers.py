from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, Contact, Interaction, Stage, Lead

STAGE_THRESHOLD_LOW = 1000
STAGE_THRESHOLD_MEDIUM = 10000


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


class LeadSerializer(serializers.ModelSerializer):
    """Serializer for Lead model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)

    WIN_SCORE_FIELDS = {'estimated_value', 'status', 'phone', 'company'}

    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at', 'win_score')

    def _calculate_win_score(self, instance):
        """Calculate and cache win_score for a lead"""
        from .ml_service import predict_win_score
        return predict_win_score(instance)

    def validate(self, data):
        """Ensure at least one stage exists before creating a lead"""
        if self.instance is None and not Stage.objects.exists():
            raise serializers.ValidationError(
                "Cannot create lead: no stages exist. Please create a stage first."
            )
        return data

    def create(self, validated_data):
        if validated_data.get('stage') is None:
            estimated_value = validated_data.get('estimated_value') or 0
            validated_data['stage'] = self.get_stage_by_value(estimated_value)
        
        instance = super().create(validated_data)
        
        # Calculate win_score on create
        instance.win_score = self._calculate_win_score(instance)
        instance.save(update_fields=['win_score'])
        
        return instance

    def update(self, instance, validated_data):
        # Check if any win_score-affecting fields are being updated
        recalculate = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in self.WIN_SCORE_FIELDS
        )
        
        instance = super().update(instance, validated_data)
        
        # Recalculate win_score only if relevant fields changed
        if recalculate:
            instance.win_score = self._calculate_win_score(instance)
            instance.save(update_fields=['win_score'])
        
        return instance
    
    def get_stage_by_value(self, value):
        """Assign stage based on estimated dollar amount using first 3 stages"""
        stages = list(Stage.objects.order_by('order')[:3])
        
        if not stages:
            return None
        
        if value < STAGE_THRESHOLD_LOW:
            return stages[0]
        elif value < STAGE_THRESHOLD_MEDIUM:
            return stages[1] if len(stages) >= 2 else stages[0]
        else:
            return stages[2] if len(stages) >= 3 else stages[-1]
