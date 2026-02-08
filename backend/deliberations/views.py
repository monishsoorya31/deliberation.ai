
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse

import json
import redis
from django.conf import settings

from .models import Conversation, Message
from .serializers import StartDeliberationSerializer, MessageSerializer, ConversationSerializer
from .tasks import run_deliberation_task
from utils.security import store_api_keys

class StartDeliberationView(APIView):
    def post(self, request):
        serializer = StartDeliberationSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            keys = serializer.validated_data['api_keys']
            
            # Create Conversation
            convo = Conversation.objects.create(title=question[:50])
            convo_id = str(convo.id)
            
            # Store Keys Securely
            store_api_keys(convo_id, keys)
            
            # Launch Celery Task
            # Pass keys explicitly? Or rely on stored ones? 
            # We already stored them. `run_deliberation_task` receives dict? 
            # `run_deliberation_task` expects `api_keys` argument in my definition?
            # Let's check `tasks.py`. Yes it takes `api_keys`.
            # But safer to just pass ID and have task fetch them?
            # Actually, passing dict to Celery persists keys in broker task payload (Redis).
            # This is risky if broker is persistent or monitored.
            # Best practice: Do NOT pass keys as task args if possible.
            # I will modify `tasks.py` to fetch from `utils.security.get_api_keys(id)`.
            # Since I already implemented `get_api_keys` logic inside `nodes.py` using `get_keys(state)`,
            # I don't need to pass them to `run_deliberation_task`.
            # I should update `tasks.py` signature to remove api_keys.
            
            max_rounds = serializer.validated_data.get('max_rounds', 3)
            
            run_deliberation_task.delay(convo_id, question, max_rounds) # Pass conversational ID, question and max_rounds
            
            return Response({"conversation_id": convo_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageStreamView(View):
    def get(self, request, conversation_id):
        print(f"DEBUG: SSE Stream Requested for {conversation_id}")
        # Verify conversation exists
        get_object_or_404(Conversation, id=conversation_id)
        
        def event_stream():
            redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            pubsub = redis_client.pubsub()
            channel_name = f"conversation_{conversation_id}"
            pubsub.subscribe(channel_name)
            
            # Send initial ping to keep alive
            yield f"event: ping\ndata: connected\n\n"
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    data = message['data']
                    # data is bytes, need to decode
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    yield f"event: message\ndata: {data}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no' # For Nginx
        return response

class ConversationHistoryView(APIView):
    def get(self, request, conversation_id):
        convo = get_object_or_404(Conversation, id=conversation_id)
        messages = Message.objects.filter(conversation=convo).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
