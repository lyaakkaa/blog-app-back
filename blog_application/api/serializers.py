from rest_framework import serializers
from .models import User, Topic, Post, Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            'avatar': {'required': False},
            'age': {'required': False, 'allow_null': True},
            'location': {'required': False}
        }
    def get_avatar(self, obj):
        request = self.context.get('request')  # Access the current request from the context
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name']  

class PostSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())

    class Meta:
        model = Post
        fields = ['id', 'pub_date', 'rating', 'commentary', 'is_liked', 'like_count', 'user', 'topic']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        representation['topic'] = TopicSerializer(instance.topic).data
        return representation





class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()  
    receiver = UserSerializer()  

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'text', 'timestamp', 'is_bot_response']
