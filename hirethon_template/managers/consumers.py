import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Handle WebSocket connection
        """
        # Get the user from the query parameters or headers
        self.user = await self.get_user_from_scope()
        
        if self.user and self.user.is_manager and self.user.is_active:
            self.admin_group_name = 'admin_notifications'
            
            # Join admin notifications group
            await self.channel_layer.group_add(
                self.admin_group_name,
                self.channel_name
            )
            
            await self.accept()
            print(f"Admin user {self.user.name} connected to notifications WebSocket")
        else:
            print("Unauthorized WebSocket connection attempt")
            await self.close()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'admin_group_name'):
            # Leave admin notifications group
            await self.channel_layer.group_discard(
                self.admin_group_name,
                self.channel_name
            )
            print(f"Admin user disconnected from notifications WebSocket. Code: {close_code}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages (for future use)
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'status': 'connected'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def send_notification(self, event):
        """
        Send notification to WebSocket
        """
        message = event['message']
        notification_data = event.get('data', {})
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message,
            'data': notification_data,
            'timestamp': event.get('timestamp')
        }))

    async def send_alert(self, event):
        """
        Send alert notification to WebSocket
        """
        alert_data = event.get('data', {})
        
        await self.send(text_data=json.dumps({
            'type': 'empty_slot_alert',
            'data': alert_data,
            'timestamp': event.get('timestamp')
        }))

    @database_sync_to_async
    def get_user_from_scope(self):
        """
        Extract and verify user from WebSocket scope
        """
        try:
            # Get user from session if available
            if 'user' in self.scope and self.scope['user'].is_authenticated:
                return self.scope['user']
            
            # Try to get token from query parameters
            query_string = self.scope.get('query_string', b'').decode()
            if query_string:
                # Parse query parameters
                params = {}
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
                
                # Check for token in query params
                token = params.get('token')
                if token:
                    try:
                        # Validate JWT token
                        access_token = AccessToken(token)
                        user_id = access_token['user_id']
                        user = User.objects.get(id=user_id)
                        return user
                    except (InvalidToken, TokenError, User.DoesNotExist):
                        pass
            
            return None
        except Exception as e:
            print(f"Error getting user from scope: {e}")
            return None
