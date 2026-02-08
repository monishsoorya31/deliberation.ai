
from django.db import models
import uuid

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title[:50]} ({self.id})"

class Message(models.Model):
    AGENT_CHOICES = [
        ('user', 'User'),
        ('openai', 'OpenAI'), # GPT
        ('gemini', 'Gemini'),
        ('deepseek', 'DeepSeek'),
        ('arbiter', 'Arbiter'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    agent_name = models.CharField(max_length=50, choices=AGENT_CHOICES) 
    content = models.TextField()
    round_number = models.IntegerField(default=0) # 0 for initial question
    timestamp = models.DateTimeField(auto_now_add=True)
    is_internal_thought = models.BooleanField(default=False)
    
    # Metadata for structured output from agents (e.g. confidence score)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"Round {self.round_number} - {self.agent_name}: {self.content[:30]}..."
