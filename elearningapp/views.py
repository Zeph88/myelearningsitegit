from django.shortcuts import render
from .models import *
from .forms import *
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .tasks import *
import json
from django.utils.safestring import mark_safe

# Redirect to Home page view
def HomePage(request, visited_user=None):

    # The view is used for both users accessing their own wall and teachers navigating to other users' wall.
    # 'visited_user' is an argument passed to the URL when a teacher access to a wall other than his/her personal one.
    # If no argument is passed, the variable takes the user id as a default.
    if visited_user is None and request.user.is_authenticated and request.user.is_superuser==0:
        visited_user = request.user.pk

    myUser = request.user

    if visited_user != None:
        # Query information linked to the user logged in
        myprofile_form = AppUser.objects.get(user=myUser.pk)
        # Query information linked to the profile that is being visited
        profile_form = AppUser.objects.get(user=visited_user)
        # Query User information linked to the profile that is being visited
        active_user = User.objects.get(pk=visited_user)
        # Load updates information using a try to prevent errors in case of empty results.
        try:
            comments = Updates.objects.filter(user=profile_form).order_by('-date_message')
        except ObjectDoesNotExist:
             comments = None
        # The page contains a form that require the POST query to trigger if submitted
        if request.method == 'POST':
            form = UpdateForm(request.POST)

            if form.is_valid():
                message = form.cleaned_data.get('message')
                update = Updates(message=message, user=profile_form)
                update.save()
        else:
            form = UpdateForm()

        return render(request, 'home.html', { 'form': form, 'profile_form': profile_form, 'my_profile_form': myprofile_form, 
                                             'user': myUser, 'who': active_user, 'comments': comments })
    return render(request, 'home.html')

# Points to add course page, following 'Course management' reference link.
def add_course(request):
    myUser = request.user
    role = AppUser.objects.get(user=request.user.pk)
    if role.status == '2':
        form = CourseForm()
        return render(request, 'add_course.html', {'form': form, 'user': myUser})
    else:
        return redirect('home')

# Points to regitering page
def register(request):

    # Default value
    registered = False
    if request.method == 'POST':
        # Two distinct forms. The first one updates auth_user. The second updates any extended fields not available in the default table. 
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        # Verify both forms are valid
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            make_thumbnail.delay(profile.pk)
            registered = True
        else:
            print(user_form.errors, profile_form.errors)

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request, 'register.html',
                  {'user_form': user_form,
                    'profile_form': profile_form,
                    'registered': registered})

def user_login(request):
    # Log in relies on POST method
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        # Ensure the user does exist and retrieve any useful information from AppUser
        user = authenticate(username=username, password=password)
        app_user = AppUser.objects.get(user_id=user.id)

        # Triggers if the user trying to log in actually exists in the DB.
        if user:
            if user.is_active and app_user.active:
                login(request, user)
                profile_form = AppUser.objects.get(user=user.pk)
                return HttpResponseRedirect('../', {'profile_form': profile_form})
            else:
                return HttpResponse("Your account is disabled.")
        else:
            return HttpResponse("Invalid login details supplied.")
    else:
        return render(request, 'login.html')

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('../')

@login_required
def manage_course(request, pk):

    # Query useful information
    material_form = MaterialForm()
    conversations = Forums.objects.filter(channel=pk).order_by('date_message')
    courseinfo = Courses.objects.get(pk=pk)
    userinfo = User.objects.get(pk=request.user.pk)
    profileinfo = AppUser.objects.get(user=request.user)

    # List all the messages ever posted on the chat and prepare them in a JSON list
    data = [
        {
            "channel": msg.channel_id,
            "user": msg.user.user.username,
            "message": msg.message,
            "timestamp": msg.date_message.strftime('%Y-%m-%d %H:%M:%S')
        }
        for msg in conversations
    ]

    # Prepare a JSON including the course and the teacher IDs
    course = [
        {
            "id": courseinfo.pk,
            "teacher": courseinfo.teacher.pk
        }
    ]

    # Prepare a JSON including the username information
    current_user ={
        'username': userinfo.username
    }

    # Triggers if the user is a student
    if profileinfo.status == '1':
        
        # Collect the student enrol information and prepare data in a JSON
        try:
            enrol = Enrol.objects.get(student__user_id=request.user.pk, course=courseinfo.pk)
            enrolinfo = [
                {
                    "student": enrol.student.user.username,
                    "course": enrol.course.title,
                    "feedback": enrol.feedback
                }
            ]
        except:
            enrolinfo = None

        # Return a boolean informing whether the student is actually enrolled to the class
        if enrolinfo is not None:
            enrolled = True
        else:
            enrolled = False
    # Triggers for teachers. By default, enrol table is out of scope for them
    else:
        enrolinfo = None
        enrolled = False

    return render(request, 'course.html', {
        'id': pk,
        'course': json.dumps(course),
        'conversations': json.dumps(data),
        'current_user': json.dumps(current_user),
        'profile': profileinfo,
        'material_form': material_form,
        'enrolled' : enrolled,
        'enrolinfo': json.dumps(enrolinfo) if enrolinfo else "[]"
    })


def social_network(request):
    user_info = AppUser.objects.get(user=request.user.pk)
    myUser = request.user
    # defines the status of the user (teacher or student)
    if user_info.status == '2':
        role = 'teacher'
        # Assign the role to a variable to be passed to the HTML
        role_json = mark_safe(json.dumps(role))
        return render(request, 'network.html', {'role': role_json, 'user': myUser})
    
    return redirect('home')
