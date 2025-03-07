from django import forms
from django.forms import ModelForm
from .models import *

# Used to update the User table. Used for registering.
class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

# Used to update the User table. Used for registering.
class UserProfileForm(forms.ModelForm):

    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})  
    )

    class Meta:
        model = AppUser
        fields = ('first_name', 'surname', 'birth_date', 'image', )

# Used to update the Updates table. Used for posting status on the user home pages.
class UpdateForm(forms.ModelForm):
    class Meta:
        model = Updates
        fields = ('message', )

# Used to update the CourseMaterial table. Used for adding new document to a course.
class MaterialForm(forms.ModelForm):
    course = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = CourseMaterial
        fields = ('material', 'course', 'document_name')

# Used to update the Courses table. Used for creating new courses.
class CourseForm(ModelForm):

    # Filters the user field to teachers only
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = AppUser.objects.filter(status='2')

    def clean(self):
        cleaned_data = super(CourseForm, self).clean()
        return(cleaned_data)

    class Meta:
        model = Courses
        fields = ['title', 'description', 'teacher', 'location', 'duration']
