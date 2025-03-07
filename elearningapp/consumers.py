import json
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import *
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        if self.user.is_authenticated:
            self.app_user = await self.get_app_user(self.user)
        else:
            self.app_user = None

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
    
    @database_sync_to_async
    def get_app_user(self, auth_user):
        return AppUser.objects.get(user=auth_user)
        
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        room_name = self.room_name
        try:
            text_data_json = json.loads(text_data)  
            message = text_data_json.get('message', '')
        except json.JSONDecodeError:
            return

        async with aiohttp.ClientSession() as session:
            url = 'http://localhost:8080/api/messages/' 
            payload = {
                'channel': room_name,
                'user': self.app_user.pk,
                'message': message
            }
            print("Sending payload:", payload)

            async with session.post(url, json=payload) as resp:
                if resp.status != 201:
                    print("Error when submitting message through api")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'user': self.user.username,
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'user': user,
            'message': message
        }))

class FeedbackConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'feedback_%s' % self.room_name
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        room_name = self.room_name
        try:
            text_data_json = json.loads(text_data)  
            feedback = text_data_json.get('feedback', '')
        except json.JSONDecodeError:
            return

        async with aiohttp.ClientSession() as session:
            url = 'http://localhost:8080/api/enrol/' 
            payload = {
                'course': room_name,
                'user': self.user.pk,
                'feedback': feedback
            }
            print("Sending payload:", payload)

            async with session.put(url, json=payload) as resp:
                if resp.status != 200:
                    print("Error when submitting feedback through api")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'feedback_message',
                'user': self.user.username,
                'feedback': feedback
            }
        )

    # Receive message from room group
    async def feedback_message(self, event):
        feedback = event['feedback']
        user = event['user']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'user': user,
            'feedback': feedback
        }))

class ConnectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        enrolled_courses = await self.get_enrolled_course_ids(self.user)

        self.course_groups = [f"course_{course_id}" for course_id in enrolled_courses]

        # For each course the student is enrolled to, pass the course id to the group
        for group in self.course_groups:
            await self.channel_layer.group_add(
                group,
                self.channel_name
            )

        teaching_courses = await self.get_teaching_course_ids(self.user)

        self.course_groups = [f"course_{id}" for id in teaching_courses]

        # For each course the teacher gives, pass the course id to the group
        for group in self.course_groups:
            await self.channel_layer.group_add(
                group,
                self.channel_name
            )

        await self.accept()
        
    async def disconnect(self, close_code):
        for group in self.course_groups:
            await self.channel_layer.group_discard(
                group,
                self.channel_name
            )

    async def receive(self, text_data):
        pass

    async def connect_message(self, event):

        user = event['user']

        app_user = await sync_to_async(AppUser.objects.get)(user=user)

        # This consumer is used for both teachers and students. However, the notification type changes depending on who is connected to the home page.
        # the condition validates that 'doc_name' is part of the fields. If it is, the notification targets a student 
        if 'doc_name' in event:

            doc_name = event['doc_name']
            room_name = event['room_name']
            course = event['course']
            material = event['material']
            
            await self.send(text_data=json.dumps({
                'user' : user,
                'doc_name' : doc_name,
                'room_name' : room_name,
                'course' : course,
                'material' : material
            }))

        # Other notifications targets teachers
        else:
            student = event['student']
            room_name = event['room_name']
            course = event['course']

            await self.send(text_data=json.dumps({
                'user' : user,
                'student' : student,
                'room_name' : room_name,
                'course' : course
            }))

    # Generates the list of courses a student is enrolled to
    async def get_enrolled_course_ids(self, user):
        app_user = await sync_to_async(AppUser.objects.get)(user=user)
        enrolled_courses = await sync_to_async(
            lambda: list(
                Enrol.objects.filter(student=app_user).values_list('course_id', flat=True)
            )
        )()
        return enrolled_courses
    
    # Generates the list of courses a teacher gives
    async def get_teaching_course_ids(self, user):
        app_user = await sync_to_async(AppUser.objects.get)(user=user)
        teaching_courses = await sync_to_async(
            lambda: list(
                Courses.objects.filter(teacher=app_user).values_list('id', flat=True)
            )
        )()
        return teaching_courses
