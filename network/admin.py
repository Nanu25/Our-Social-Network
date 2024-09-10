from django.contrib import admin

# Register your models here.

from .models import User, Post

class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "content", "timestamp")


admin.site.register(User)
admin.site.register(Post, PostAdmin)