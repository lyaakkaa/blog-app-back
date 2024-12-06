from django.contrib import admin
from .models import User, Topic, Post, Message

admin.site.register(User)
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(Message)