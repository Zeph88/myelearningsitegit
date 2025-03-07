import factory
from random import randint
from random import choice
import random
import datetime

from django.test import TestCase
from django.conf import settings
from django.core.files import File
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: "jbrown")
    email = factory.LazyAttribute(lambda _: 'jbrown@unionjack.uk')
    password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')


class AppUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    first_name = "John"
    surname = "Brown"
    birth_date = "1950-01-01"
    status = choice(['1', '2'])
    active = factory.LazyFunction(lambda: random.choice([True, False]))

    class Meta:
        model = AppUser


class CoursesFactory(factory.django.DjangoModelFactory):
    title = "IT Engineer class"
    description = "Learn the basics of IT Engineering"
    teacher = factory.SubFactory(AppUserFactory)
    location = "UK"
    duration = randint(1, 100000)
    active = factory.LazyFunction(lambda: random.choice([True, False]))

    class Meta:
        model = Courses

class CourseMaterialFactory(factory.django.DjangoModelFactory):
    course = factory.SubFactory(CoursesFactory)
    document_name = "New Document"
    date_material = factory.LazyFunction(datetime.date.today)

    class Meta:
        model = CourseMaterial

class EnrolFactory(factory.django.DjangoModelFactory):
    course = factory.SubFactory(CoursesFactory)
    student = factory.SubFactory(AppUserFactory)
    feedback = "Good"

    class Meta:
        model = Enrol

class UpdatesFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(AppUserFactory)
    message = "Hello world !"
    date_message = factory.LazyFunction(datetime.date.today)

    class Meta:
        model = Updates

class ForumsFactory(factory.django.DjangoModelFactory):
    channel = factory.SubFactory(CoursesFactory)
    user = factory.SubFactory(AppUserFactory)
    message = "Hey!"
    date_message = factory.LazyFunction(datetime.date.today)

    class Meta:
        model = Forums
