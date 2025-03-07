from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

# Serialize the User's information saved in auth_user
class CoreUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

# Serialize the AppUser's information saved in AppUser
class UserSerializer(serializers.ModelSerializer):

    user = CoreUserSerializer()

    class Meta:
        model = AppUser
        fields = ['user', 'first_name', 'surname', 'birth_date', 'status', 'active', 'image']


# Serialize the Courses' information. Used for POST API.
class CoursesSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=AppUser.objects.all())

    class Meta:
        model = Courses
        fields = ['id', 'title', 'description', 'teacher', 'location', 'duration', 'active']

    def create(self, validated_data):
        return Courses.objects.create(**validated_data)

    def update(self, instance, validated_data):
        teacher_data = self.initial_data.get('teacher')
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.location = validated_data.get('location', instance.location)
        instance.duration = validated_data.get('duration', instance.duration)
        instance.active = validated_data.get('active', instance.active)
        instance.teacher = AppUser.objects.get(pk=teacher_data['id'])
        instance.save()
        return instance

# Serialize the Courses' information. Used to return the course list
class CoursesListSerializer(serializers.ModelSerializer):
    teacher = UserSerializer()

    class Meta:
        model = Courses
        fields = ['id', 'title', 'description', 'teacher', 'location', 'duration', 'active']

# Serialize the Forums' information. Used to return the conversation history held in courses' forums.
class ForumSerializer(serializers.ModelSerializer):

    username = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(queryset=AppUser.objects.all())

    class Meta:
        model = Forums
        fields = ['channel', 'user', 'username', 'message', 'date_message']
    
    def get_username(self, obj):
        return obj.user.user.username

# Serialize the Material' information.
class MaterialSerializer(serializers.ModelSerializer):

    course = serializers.PrimaryKeyRelatedField(queryset=Courses.objects.all())
    course_info = CoursesListSerializer(source='course', read_only=True)

    class Meta:
        model = CourseMaterial
        fields = ['id','course','course_info', 'material', 'document_name']

# Serialize the Enrol information.
class EnrolSerializer(serializers.ModelSerializer):

    course = serializers.PrimaryKeyRelatedField(queryset=Courses.objects.all())
    course_info = CoursesListSerializer(source='course', read_only=True)
    student = serializers.PrimaryKeyRelatedField(queryset=AppUser.objects.all())
    student_info = UserSerializer(source='student', read_only=True)
    feedback = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Enrol
        fields = ['course', 'course_info', 'student', 'student_info', 'feedback']
    