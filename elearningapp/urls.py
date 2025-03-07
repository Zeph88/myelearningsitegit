from django.urls import include, path
from . import views
from . import api
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', views.HomePage, name='home'),
    path('<int:visited_user>/', login_required(login_url='login')(views.HomePage), name='wall'),
    path('social_network/', login_required(login_url='login')(views.social_network), name='network'),
    path('api/social_network/', api.AllUsers.as_view(), name='all_users'),
    path('api/enrol/', api.EnrolUser.as_view(), name='enrol'),
    path('api/material/', api.MaterialDetail.as_view(), name='upload'),
    path('api/material/<int:user>/', api.MaterialNotif.as_view(), name='push_material'),
    path('api/enrol/<int:user>/', api.EnrolNotif.as_view(), name='enrol'),
    path('api/courses/', api.CourseList.as_view(), name='see_course'),
    path('api/blockuser/<int:user>/', api.BlockUser.as_view(), name='block_user'),
    path('api/create_course/', api.CoursesDetail.as_view(), name='add_course_api'),
    path('create_course/', login_required(login_url='login')(views.add_course), name='add_course'),
    path('api/messages/', api.ForumDetails.as_view(), name='message_forum'),
    path('course/<int:pk>/', login_required(login_url='login')(views.manage_course), name='manage'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
