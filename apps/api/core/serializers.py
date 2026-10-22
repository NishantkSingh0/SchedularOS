from rest_framework import serializers
from core.models import Organization, Brand, UserProfile, Lead, ConsentRecord


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'settings']
        read_only_fields = ['id']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'voice', 'rules', 'colors', 'logo_url']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    org = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'org', 'role']
        read_only_fields = ['id', 'user', 'org']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'email', 'phone', 'stage', 'score', 'tags',
            'has_whatsapp_consent', 'has_email_consent', 'opted_out_at',
            'last_contacted_at'
        ]
        read_only_fields = ['id', 'last_contacted_at']


class ConsentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRecord
        fields = ['id', 'lead', 'channel', 'consented', 'source']
        read_only_fields = ['id']
