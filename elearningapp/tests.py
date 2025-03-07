import json
from django.test import TestCase
from django.urls import reverse
from django.urls import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path, re_path
from .consumers import *
from channels.auth import AuthMiddlewareStack
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase
from rest_framework import status
from .model_factories import *
from .serializers import *
import pytest
import urllib.parse

class AppUserSerialiserTest(APITestCase):
    user1 = None
    userserializer = None
    appuser1 = None
    appuserserializer = None

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John')
        self.appuserserializer = UserSerializer(instance=self.appuser1)

    def tearDown(self):
        AppUser.objects.all().delete()
        Courses.objects.all().delete()
        CourseMaterial.objects.all().delete()
        Enrol.objects.all().delete()
        Updates.objects.all().delete()
        Forums.objects.all().delete()
        AppUserFactory.reset_sequence(0)
        CoursesFactory.reset_sequence(0)
        CourseMaterialFactory.reset_sequence(0)
        EnrolFactory.reset_sequence(0)
        UpdatesFactory.reset_sequence(0)
        ForumsFactory.reset_sequence(0)

    def test_appuserSerialiserHasCorrectFields(self):
        data = self.appuserserializer.data
        self.assertEqual(set(data.keys()), set(['user', 'first_name',
                                                'surname', 'birth_date', 'status',
                                                'active', 'image']))

    def test_SerialiserAppuserIDIsHasCorrectData(self):
        data = self.appuserserializer.data
        self.assertEqual(data['user']['username'], "jbrown2")
        self.assertEqual(data['first_name'], "John")

class CoursesSerialiserTest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John')
        self.course1 = CoursesFactory.create(pk=1, teacher=self.appuser1, title='IT Engineering')
        self.courseserializer = CoursesSerializer(instance=self.course1)

    def test_courseSerialiserHasCorrectFields(self):
        data = self.courseserializer.data
        self.assertEqual(set(data.keys()), set(['id', 'title', 'description',
                                                'teacher', 'location', 'duration',
                                                'active']))

    def test_SerialiserCourseIDIsHasCorrectData(self):
        data = self.courseserializer.data
        self.assertEqual(data['teacher'], 1)

class Navigation(APITestCase):

    good_url = ''
    bad_url = ''

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John', status='2')
        self.user2 = User.objects.create_user(username="daisyM", password="test")
        self.appuser2 = AppUserFactory.create(pk=2, user=self.user2, first_name='Daisy', status='1')
        self.course1 = CoursesFactory.create(pk=1, teacher=self.appuser1, title='IT Engineering')
        self.courseserializer = CoursesSerializer(instance=self.course1)
        self.good_url_home = reverse('home')
        self.good_url_wall = reverse('wall', kwargs={'visited_user':1})
        self.bad_url_wall = '/g/'
        self.bad_url_course = '/course/g/'
        self.good_url_course = '/course/1/'
        self.block_url = '/api/blockuser/2/'
        self.url_create_course = reverse('add_course')

    def test_getuserdetails(self):
        self.client.login(username="jbrown2", password="gstq")
        response = self.client.get(self.good_url_home)
        self.assertEqual(response.status_code, 200)
    
    def test_getuserwalldetails_valid(self):
        self.client.login(username="jbrown2", password="gstq")
        response = self.client.get(self.good_url_wall)
        self.assertEqual(response.status_code, 200)
    
    def test_getuserwalldetails_invalid(self):
        self.client.login(username="jbrown2", password="gstq")
        response = self.client.get(self.bad_url_wall)
        self.assertEqual(response.status_code, 404)

    def test_getcoursedetails_invalid(self):
        self.client.login(username="jbrown2", password="gstq")
        response = self.client.get(self.bad_url_course)
        self.assertEqual(response.status_code, 404)

    # Test page redirection if the user is not loggued in
    def test_getcoursedetails_nonlogged(self):
        response = self.client.get(self.good_url_course)
        self.assertEqual(response.status_code, 302)
    
    # Test page redirection if the user is loggued in
    def test_getcoursedetails_logged(self):
        self.client.login(username="jbrown2", password="gstq")
        response = self.client.get(self.good_url_course)
        self.assertEqual(response.status_code, 200)

    # Test that a user cannot reconnect after being blocked. It returns 302 instead of a 403 due to a redirection.
    def test_blocked_student_access(self):
        self.client.login(username="jbrown2", password="gstq")
        response = self.client.put(self.block_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.logout()
        logged_in = self.client.login(username="DaisyM", password="test")
        response = self.client.get(self.good_url_course)
        self.assertEqual(response.status_code, 302)

    def test_canteachercreatecourses(self):
        self.client.login(username="jbrown2", password="gstq")
        response = self.client.get(self.url_create_course)
        self.assertEqual(response.status_code, 200)
    
    def test_arestudentsredirected(self):
        self.client.login(username="DaisyM", password="test")
        response = self.client.get(self.url_create_course)
        self.assertEqual(response.status_code, 302)

class AppUserAPITest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John')
        self.url = reverse('all_users')
    
    def test_get_appuser(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

class CoursesAPITest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John')
        self.course = CoursesFactory.create(pk=1, teacher=self.appuser1, title='It Engineering')
        self.url_post = reverse('add_course_api')
        self.url_get = reverse('see_course')

    def tearDown(self):
        AppUser.objects.all().delete()
        Courses.objects.all().delete()
        CourseMaterial.objects.all().delete()
        Enrol.objects.all().delete()
        Updates.objects.all().delete()
        Forums.objects.all().delete()
        AppUserFactory.reset_sequence(0)
        CoursesFactory.reset_sequence(0)
        CourseMaterialFactory.reset_sequence(0)
        EnrolFactory.reset_sequence(0)
        UpdatesFactory.reset_sequence(0)
        ForumsFactory.reset_sequence(0)
    
    def test_post_course(self):
        data = {
            'teacher': self.appuser1.id,
            'title': 'Test Course',
            'description': 'test',
            'location': 'UK',
            'duration': 100,
            'active': True
        }
        response = self.client.post(self.url_post, data, format='json')
        #302 instead of 201 as the API triggers a redirect
        self.assertEqual(response.status_code, 302)  
        self.assertTrue(Courses.objects.filter(title='Test Course').exists())

    def test_post_incorrect_course(self):
        data = {
            'teacher': self.appuser1.id,
            # empty title
            'title': '',
            'description': 'test',
            'location': 'UK',
            'duration': 100,
            'active': True
        }
        response = self.client.post(self.url_post, data, format='json')
        #302 instead of 201 as the API triggers a redirect
        self.assertEqual(response.status_code, 400)

        
    def test_get_course(self):
        response = self.client.get(self.url_get)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

class ForumAPITest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John')
        self.user2 = User.objects.create_user(username="daisyM", password="http")
        self.appuser2 = AppUserFactory.create(pk=2, user=self.user2, first_name='Daisy')
        self.course = CoursesFactory.create(pk=1, teacher=self.appuser1, title='It Engineering')
        self.url_post = reverse('message_forum')

    def tearDown(self):
        AppUser.objects.all().delete()
        Courses.objects.all().delete()
        CourseMaterial.objects.all().delete()
        Enrol.objects.all().delete()
        Updates.objects.all().delete()
        Forums.objects.all().delete()
        AppUserFactory.reset_sequence(0)
        CoursesFactory.reset_sequence(0)
        CourseMaterialFactory.reset_sequence(0)
        EnrolFactory.reset_sequence(0)
        UpdatesFactory.reset_sequence(0)
        ForumsFactory.reset_sequence(0)
    
    def test_post_message(self):
        data = {
            'channel': self.course.id,
            'user': self.user1.id,
            'message': 'hello world!'
        }
        response = self.client.post(self.url_post, data, format='json')
        self.assertEqual(response.status_code, 201)  
        self.assertTrue(Forums.objects.filter(message='hello world!').exists())


class CourseMaterialAPITest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John')
        self.course = CoursesFactory.create(pk=1, teacher=self.appuser1, title='It Engineering')
        self.url_post = reverse('upload')

    def tearDown(self):
        AppUser.objects.all().delete()
        Courses.objects.all().delete()
        CourseMaterial.objects.all().delete()
        Enrol.objects.all().delete()
        Updates.objects.all().delete()
        Forums.objects.all().delete()
        AppUserFactory.reset_sequence(0)
        CoursesFactory.reset_sequence(0)
        CourseMaterialFactory.reset_sequence(0)
        EnrolFactory.reset_sequence(0)
        UpdatesFactory.reset_sequence(0)
        ForumsFactory.reset_sequence(0)
    
    def test_post_material(self):
        dummy_file = SimpleUploadedFile(
            "test_file.txt",
            b"File content",
            content_type="text/plain"
        )
        data = {
            'course': self.course.id,
            'document_name': "doc test",
            'material': dummy_file
        }
        response = self.client.post(self.url_post, data, format='multipart')
        self.assertEqual(response.status_code, 201)  
        self.assertTrue(CourseMaterial.objects.filter(document_name='doc test').exists())


class EnrolAPITest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="jbrown2", password="gstq")
        self.appuser1 = AppUserFactory.create(pk=1, user=self.user1, first_name='John')
        self.user2 = User.objects.create_user(username="daisyM", password="http")
        self.appuser2 = AppUserFactory.create(pk=2, user=self.user2, first_name='Daisy')
        self.course = CoursesFactory.create(pk=1, teacher=self.appuser1, title='It Engineering')
        self.enroluser2 = EnrolFactory.create(pk=1, student=self.appuser2, course=self.course)
        self.url_base = reverse('enrol')
        self.url_post = f"{self.url_base}?course={self.course.id}&user={self.appuser1.id}"
        self.url_delete = f"{self.url_base}?course={self.course.id}&user={self.appuser2.id}"


    def tearDown(self):
        AppUser.objects.all().delete()
        Courses.objects.all().delete()
        CourseMaterial.objects.all().delete()
        Enrol.objects.all().delete()
        Updates.objects.all().delete()
        Forums.objects.all().delete()
        AppUserFactory.reset_sequence(0)
        CoursesFactory.reset_sequence(0)
        CourseMaterialFactory.reset_sequence(0)
        EnrolFactory.reset_sequence(0)
        UpdatesFactory.reset_sequence(0)
        ForumsFactory.reset_sequence(0)
    
    def test_post_enrol(self):
        
        data = {
            'course': self.course.id,
            'student': self.appuser1.id
        }
        response = self.client.post(self.url_post, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Enrol.objects.filter(course=self.course.id, student=self.appuser1.id).exists())
    
    def test_leavefeedback_enrol(self):
        data = {
            'course': self.course.id,
            'user': self.appuser2.id,
            'feedback': 'good course'
        }
        response = self.client.put(self.url_base, data, format='json')
        self.assertEqual(response.status_code, 200)
        check_feedback = Enrol.objects.get(student=self.appuser2, course=self.course)
        self.assertEqual(check_feedback.feedback, 'good course')
    
    def test_delete_enrol(self):
            
        response = self.client.delete(self.url_delete)
        self.assertEqual(response.status_code, 204)

### ASYNCHRONOUS TESTS ### 
application = AuthMiddlewareStack(
    URLRouter([
        re_path(r"ws/connect/(?P<user_id>\w+)/$", ConnectConsumer.as_asgi()),
        re_path(r"ws/feedback/(?P<room_name>\w+)/$", FeedbackConsumer.as_asgi()),
        re_path(r"ws/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
    ])
)

@pytest.fixture
def test_user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="test")

@pytest.fixture
def test_app_user(db, test_user):
    return AppUser.objects.create(user=test_user, first_name="Test", surname="User", birth_date="1950-01-01", status="1", active=True)

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_connect_consumer(test_user, test_app_user):

    communicator = WebsocketCommunicator(application, "/ws/connect/1/")

    communicator.scope["user"] = test_user
    
    connected, subprotocol = await communicator.connect()
    assert connected, "Connection to consumer failed"
    
    await communicator.disconnect()


class DummyResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

class DummyClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def put(self, url, json):
        return DummyResponse()

@pytest.fixture
def dummy_session(monkeypatch):
    monkeypatch.setattr(aiohttp, "ClientSession", DummyClientSession)

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_feedback_consumer(test_user, dummy_session):
    communicator = WebsocketCommunicator(application, "/ws/feedback/1/")
    communicator.scope["user"] = test_user

    connected, _ = await communicator.connect()
    assert connected, "Connection to consumer failed"

    message = {"feedback": "Good class!"}
    await communicator.send_to(text_data=json.dumps(message))

    response = await communicator.receive_from()
    data = json.loads(response)
    assert data.get("feedback") == "Good class!", "Incorrect feedback"
    assert data.get("user") == test_user.username, "Incorrect user"

    await communicator.disconnect()


class DummyResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

class DummyClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def put(self, url, json):
        return DummyResponse()

    def post(self, url, json):
        return DummyResponse()

@pytest.fixture
def dummy_session(monkeypatch):
    monkeypatch.setattr(aiohttp, "ClientSession", DummyClientSession)

@pytest.fixture
def test_user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="test")

@pytest.fixture
def test_app_user(db, test_user):
    app_user = AppUser.objects.create(
        user=test_user,
        first_name="Test",
        status="1",
        birth_date="2000-01-01"
    )
    return app_user

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_consumer(test_user, test_app_user, dummy_session):
    communicator = WebsocketCommunicator(application, "/ws/1/")
    communicator.scope["user"] = test_user

    connected, _ = await communicator.connect()
    assert connected, "Connection to consumer failed"

    message = {"message": "Hello world!"}
    await communicator.send_to(text_data=json.dumps(message))

    response = await communicator.receive_from()
    data = json.loads(response)
    assert data.get("message") == "Hello world!", "Incorrect message"
    assert data.get("user") == test_user.username, "Incorrect user"

    await communicator.disconnect()