from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import *
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework import mixins
from django.shortcuts import redirect
from django.contrib.auth.models import User
from rest_framework.generics import ListAPIView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# GET all users. Used for the social network retruning the list of all users that can be accessed by teachers.
class AllUsers(ListAPIView):
    queryset = AppUser.objects.select_related('user').all() 
    serializer_class = UserSerializer

# API to post, put and delete on the Courses table. Used to manage the table with multiple forms scattered across the application.
class CoursesDetail(mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 generics.GenericAPIView):

    queryset = Courses.objects.all()
    serializer_class = CoursesSerializer

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        return redirect('home')

    def put(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        return redirect('home')

    def delete(self, request, *args, **kwargs):
        response = self.destroy(request, *args, **kwargs)
        return redirect('home')

# API to GET the Courses records. Used to return the list of course on the left pane of app pages.
class CourseList(generics.ListAPIView):
    queryset = Courses.objects.all()
    serializer_class = CoursesListSerializer

# API to POST message to the Forum tables. It helps keeping track of the conversations that were ever held in relation to a course.
class ForumDetails(generics.CreateAPIView, generics.ListAPIView):
    queryset = Forums.objects.all()
    serializer_class = ForumSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

# API to block the user at teacher's discretion. It is a PUT, not a DELETE. It updates the user's status from active True to False, or the reverse. 
class BlockUser(generics.GenericAPIView):
    queryset = AppUser.objects.select_related('user').all() 
    serializer_class = UserSerializer
    lookup_field = 'user'

    def put(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user')  
        app_user = AppUser.objects.get(user_id=user_id)  
        if app_user.active == 1:
            app_user.active = 0
            message = f"user {user_id} has been blocked."
        else:
            app_user.active = 1
            message = f"user {user_id} has been unblocked."
        app_user.save()
        return JsonResponse({"success": True, "message": message}) 

# Retrieve and post documents in relation to a course
class MaterialDetail(mixins.ListModelMixin,
                     mixins.CreateModelMixin, 
                     mixins.DestroyModelMixin, 
                     generics.GenericAPIView):
    
    serializer_class = MaterialSerializer
    
    # By default, documents are retrieved based on their primary key. Amending this method ensures the documents are retrieved in batched, based on the course ID instead.
    def get_queryset(self):
        course_id = self.request.GET.get('room')
        return CourseMaterial.objects.filter(course_id=course_id)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # POST arguments are passed through the body of the query
        course_id = request.data.get('course')
        request.data['course'] = course_id 
        response = self.create(request, *args, **kwargs)

        doc_name = response.data.get('document_name', 'unknown Document')
        course = response.data.get('course_info', 'unknown course')
        material = response.data.get('material', 'unknown material')

        channel_layer = get_channel_layer()

        # A JSON is sent to a WebSocket to notify students that a new document in relation to the course has been uploaded.
        async_to_sync(channel_layer.group_send)(
            f"course_{course_id}",
            {
                'type': 'connect_message',
                'user': request.user.pk,
                'doc_name': doc_name,
                'room_name': course_id,
                'course' : course,
                'material' : material
            }
        )

        return Response({"message": "Document added", "course": course_id}, status=201)

    def delete(self, request, *args, **kwargs):
        material_id = self.kwargs.get('material_id') 
        material = CourseMaterial.objects.get(id=material_id)
        material.delete()
        return Response({"message": "Material deleted successfully"}, status=204)

# Contrary to previous API, MaterialNotif filters the documents in scope for a student instead of a course. 
# It is used to display the relevant documents for a student on the home page.
class MaterialNotif(mixins.ListModelMixin, 
                     generics.GenericAPIView):
    
    serializer_class = MaterialSerializer

    def get_queryset(self):
        return CourseMaterial.objects.filter(course__enrol__student__user_id = self.kwargs.get('user')).all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
# It filters the enrol status of student in scope for a teacher. 
# It is used to display the relevant status on the teacher's home page.
class EnrolNotif(mixins.ListModelMixin, 
                     generics.GenericAPIView):
    
    serializer_class = EnrolSerializer

    def get_queryset(self):
        return Enrol.objects.filter(course__teacher__user_id = self.kwargs.get('user')).all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

# The API is used to amend the Enrol table.
class EnrolUser(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                mixins.RetrieveModelMixin,
                mixins.UpdateModelMixin, 
                mixins.DestroyModelMixin, 
                generics.GenericAPIView):
    
    queryset = Enrol.objects.all()
    serializer_class = EnrolSerializer

    def post(self, request, *args, **kwargs):
        # POST API has student and course IDs passed in the URL as parameters
        course_id = request.GET.get('course')
        student_id = request.GET.get('user')
        # Once retrieved the above parameters are passed to the request data, allowing to POST the record
        request.data['course'] = course_id
        request.data['student'] = student_id 
        response = self.create(request, *args, **kwargs)
        
        student = response.data.get('student_info', 'unknown student')
        course = response.data.get('course_info', 'unknown course')


        channel_layer = get_channel_layer()

        # A JSON is sent to a WebSocket to notify the teacher of the specific course that a new student enroled.
        async_to_sync(channel_layer.group_send)(
            f"course_{course_id}",
            {
                'type': 'connect_message',
                'user': request.user.pk,
                'student': student,
                'room_name': course_id,
                'course' : course
            }
        )

        return Response({"message": "User added", "course": course_id}, status=201)
        
    # Triggers when a student cancelled the enrol
    def delete(self, request, *args, **kwargs):
        course_id = request.GET.get('course')
        student_id = request.GET.get('user')
        delete_enrol = Enrol.objects.get(student=student_id, course=course_id)
        delete_enrol.delete()
        return Response({"message": "Participation deleted successfully"}, status=204)
    
    # Triggers when a student posts a feedback in relation to the enrolled course.
    def put(self, request, *args, **kwargs):

        course_id = request.data['course']
        student_id = request.data['user']
        existing_record = Enrol.objects.get(course=course_id, student__user_id=student_id)

        feedback = request.data['feedback']
        existing_record.feedback = feedback  
        existing_record.save()

        return Response({"message": "Feedback updated successfully"}, status=200, content_type="application/json")