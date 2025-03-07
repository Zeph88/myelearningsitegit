from django.db import models
from django.contrib.auth.models import User

# Limit the user role options to student or teacher
All_status = (
    ( '1', 'student' ),
    ( '2', 'teacher' ),
)

# Extends the User table with additional fields 
class AppUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256, blank=False, null=False)
    surname = models.CharField(max_length=256, blank=False, null=False)
    birth_date = models.DateField(null=False, blank=False)
    status = models.CharField(max_length=20, choices=All_status, default='1')
    image = models.FileField(blank=True, upload_to='images')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

# All the courses available in the application
class Courses(models.Model):
    title = models.CharField(max_length=256, blank=False, null=False)
    description = models.CharField(max_length=256, blank=False, null=False)
    teacher = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    location = models.CharField(max_length=256, blank=False, null=False)
    duration = models.IntegerField(blank=False, null=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

# All the material document available for courses
class CourseMaterial(models.Model):
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    document_name = models.CharField(max_length=256, blank=False, null=False)
    material = models.FileField(null=False, upload_to='material_course')
    date_material = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.course

# Students' enrol status
class Enrol(models.Model):
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    student = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    feedback = models.CharField(max_length=256, blank=False, null=False)

    def __str__(self):
        return str(self.student)+":"+str(self.course)

# List all the comments in a user's home page
class Updates(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=256, blank=False, null=False)
    date_message = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user+":"+self.date_message+":"+self.message

# List all the conversations held in a course forum
class Forums(models.Model):
    channel = models.ForeignKey(Courses, on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=256, blank=False, null=False)
    date_message = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user+":"+self.channel+":"+self.date_message+":"+self.message

# Suggested extension of the model for user to talk to each other directly, without doing so through the course forum. Not implemented.
class Chats(models.Model):
    talkto = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name="chats_as_talkto")
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name="chats_as_user")
    message = models.CharField(max_length=256, blank=False, null=False)
    date_message = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user+":"+self.talkto+":"+self.date_message+":"+self.message