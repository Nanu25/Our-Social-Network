from django.contrib import admin

# Register your models here.

from .models import User, Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "content", "timestamp")

class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "content", "timestamp")

admin.site.register(User)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)