from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User, PQCKey

admin.site.register(User)
admin.site.register(PQCKey)