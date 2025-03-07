from django.contrib import admin
from .models import *

class AppUserAdmin(admin.ModelAdmin):
    model = AppUser

class CoursesAdmin(admin.ModelAdmin):
    model = Courses

class CourseMaterialAdmin(admin.ModelAdmin):
    model = CourseMaterial

class EnrolAdmin(admin.ModelAdmin):
    model = Enrol

class UpdatesAdmin(admin.ModelAdmin):
    model = Updates

class ForumsAdmin(admin.ModelAdmin):
    model = Forums

admin.site.register(AppUser, AppUserAdmin)
admin.site.register(Courses, CoursesAdmin)
admin.site.register(CourseMaterial, CourseMaterialAdmin)
admin.site.register(Enrol, EnrolAdmin)
admin.site.register(Updates, UpdatesAdmin)
admin.site.register(Forums, ForumsAdmin)
