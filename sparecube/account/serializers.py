from rest_framework import serializers
from .models import Utente
from django.contrib.auth.hashers import make_password

from rest_framework import serializers, viewsets, status

class SignInSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=255, required=True, write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Utente
        fields = ('id', 'id_azienda', 'first_name', 'last_name', 'username', 'email', 'password', 'account_type', 'is_active', 'is_staff', 'is_superuser')
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)

        instance.is_active = True
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Utente
        fields = ('old_password', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password" : "Password fields didn't match."})
        
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value
    
    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance
    

# test
class ChangePassword(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

# For facebook
class SocialSerializer(serializers.Serializer):
    #Serializer which accepts an OAuth2 access token and provider
    provider = serializers.CharField(max_length = 255, required=True)
    access_token = serializers.CharField(max_length=4096, required=True, trim_whitespace=True)