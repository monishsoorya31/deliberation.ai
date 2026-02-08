
from rest_framework import serializers
from .models import Conversation, Message

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'created_at', 'title', 'is_completed']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'agent_name', 'content', 'round_number', 'timestamp', 'is_internal_thought']

class StartDeliberationSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=5000)
    api_keys = serializers.DictField(child=serializers.CharField(required=False, allow_blank=True), required=True)
    max_rounds = serializers.IntegerField(min_value=1, max_value=5, default=3)
