from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Friend, User, Topic, Post, Message
from .serializers import UserSerializer, TopicSerializer, PostSerializer, MessageSerializer
import logging
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_jwt.settings import api_settings 
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from django.utils.dateparse import parse_date
from django.db import models


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=['get'], url_path='posts')
    def user_posts(self, request, pk=None):
        user = self.get_object()
        posts = Post.objects.filter(user=user) 
        
        start_date = request.query_params.get('start_date') 
        end_date = request.query_params.get('end_date')      

        if start_date:
            try:
                start_date = parse_datetime(start_date)
                posts = posts.filter(pub_date__gte=start_date)
            except ValueError:
                return Response({'error': 'Invalid start_date format. Use ISO 8601 format.'}, 
                                status=status.HTTP_400_BAD_REQUEST)

        if end_date:
            try:
                end_date = parse_datetime(end_date)
                posts = posts.filter(pub_date__lte=end_date)  
            except ValueError:
                return Response({'error': 'Invalid end_date format. Use ISO 8601 format.'}, 
                                status=status.HTTP_400_BAD_REQUEST)

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()  # This retrieves the user by the ID provided in the URL (e.g., /api/users/1/)

        # Proceed with the update for the user with the given ID in the URL
        partial = kwargs.pop('partial', False)  # Handles PATCH for partial updates
        serializer = self.get_serializer(user, data=request.data, partial=partial)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, partial=True)

    @action(detail=True, methods=['post'], url_path='toggle_favorite')
    def toggle_favorite(self, request, pk=None):
        user = self.get_object()  
        favorite_user_id = request.data.get('favorite_user_id')

        if not favorite_user_id:
            return Response({'error': 'You must provide a favorite_user_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            favorite_user = User.objects.get(id=favorite_user_id)  
        except User.DoesNotExist:
            return Response({'error': 'The user you are trying to add/remove does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if user.id == favorite_user.id:
            return Response({'error': 'You cannot add/remove yourself as a favorite.'}, status=status.HTTP_400_BAD_REQUEST)

        if favorite_user in user.favorite_users.all():
            user.favorite_users.remove(favorite_user)
            user.save()

            # Удалить дружбу
            Friend.objects.filter(
                models.Q(user1=user, user2=favorite_user) | models.Q(user1=favorite_user, user2=user)
            ).delete()

            return Response({'message': 'User removed from favorites successfully.'}, status=status.HTTP_200_OK)
        else:
            user.favorite_users.add(favorite_user)
            user.save()

            # Создать дружбу, если есть взаимная подписка
            if user in favorite_user.favorite_users.all():
                Friend.objects.get_or_create(user1=min(user, favorite_user, key=lambda u: u.id),
                                            user2=max(user, favorite_user, key=lambda u: u.id))

            return Response({'message': 'User added to favorites successfully.'}, status=status.HTTP_200_OK)

        
    @action(detail=False, methods=['post'], url_path='is_favorite')
    def is_following(self, request):
        """
        Check if the logged-in user has the specified user in their favorite list.
        """
        user_id = request.data.get('user_id')
        logged_in_user_id = request.data.get('logged_in_user_id')

        if not user_id or not logged_in_user_id:
            return Response(
                {'error': 'Both user_id and logged_in_user_id are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
     
            logged_in_user = User.objects.get(id=logged_in_user_id)
            is_following = int(user_id) in logged_in_user.favorite_users.values_list('id', flat=True)

            return Response({'is_following': is_following}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'One or both users not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='set_friend_name')
    def set_friend_name(self, request, pk=None):
        user = self.get_object()
        friend_id = request.data.get('friend_id')
        friend_name = request.data.get('friend_name')

        if not friend_id:
            return Response({'error': 'friend_id and friend_name are required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            friend = Friend.objects.get(
                models.Q(user1=user, user2_id=friend_id) | 
                models.Q(user2=user, user1_id=friend_id)
            )
        except Friend.DoesNotExist:
            return Response({'error': 'Friendship not found.'}, status=status.HTTP_404_NOT_FOUND)

        if friend.user1 == user:
            friend.user1_name_for_user2 = friend_name
        elif friend.user2 == user:
            friend.user2_name_for_user1 = friend_name

        friend.save()
        return Response({'message': 'Friend name updated successfully.'}, status=status.HTTP_200_OK)

        

    @action(detail=True, methods=['get'], url_path='friends')
    def get_friends(self, request, pk=None):
        user = self.get_object()
        friends = Friend.objects.filter(models.Q(user1=user) | models.Q(user2=user)).distinct()

        data = []
        for friendship in friends:
            if friendship.user1 == user:
                friend_data = {
                    'friend': UserSerializer(friendship.user2, context={'request': request}).data,
                    'friend_name': friendship.user1_name_for_user2,
                }
            else:
                friend_data = {
                    'friend': UserSerializer(friendship.user1, context={'request': request}).data,
                    'friend_name': friendship.user2_name_for_user1,
                }
            data.append(friend_data)

        return Response(data, status=status.HTTP_200_OK)



    

    @action(detail=True, methods=['get'], url_path='get_statistic')
    def get_statistic(self, request, pk=None):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Проверка наличия параметров
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Парсинг формата YYYY-MM-DD
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)

            if not start_date or not end_date:
                raise ValueError("Invalid date format.")
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Проверка, что start_date раньше end_date
        if start_date > end_date:
            return Response({'error': 'start_date must be earlier than end_date.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Получение пользователя
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Фильтрация постов пользователя по дате
        posts = Post.objects.filter(user=user, pub_date__gte=start_date, pub_date__lte=end_date)

        # Группировка постов по дням
        daily_stats = {}
        for post in posts:
            day = post.pub_date  # pub_date уже содержит только дату
            if day not in daily_stats:
                daily_stats[day] = 0
            daily_stats[day] += 1

        # Преобразование результата в список
        statistics = [{'date': str(day), 'count': count} for day, count in sorted(daily_stats.items())]

        return Response(statistics, status=status.HTTP_200_OK)



class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()  
        user_id = request.data.get('user_id')  

        if not user_id:
            return Response(
                {'error': 'user_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if post.user.id == user.id:
            return Response(
                {'error': 'You cannot like your own post.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        post.is_liked = not post.is_liked  
        post.like_count += 1 if post.is_liked else -1  
        post.save()

        return Response(
            {'like_count': post.like_count, 'is_liked': post.is_liked},
            status=status.HTTP_200_OK
        )


logger = logging.getLogger(__name__)
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

class SignInView(APIView):
    def post(self, request):
        try:
            login = request.data.get('login')
            password = request.data.get('password')

            logger.info(f"Received login: {login}")

            user = User.objects.filter(login=login).first()
            if user and user.password == password:  
                user.activity = now()
                user.save(update_fields=['activity']) 

                token = jwt_encode_handler(
                    {'userID': user.id, 'exp_time': int((datetime.now() + timedelta(days=1)).timestamp())}
                )

                return Response({
                    'token': str(token),
                    'id': user.id,
                }, status=status.HTTP_200_OK)
            else:
                raise AuthenticationFailed('Invalid credentials')

        except Exception as e:
            logger.error(f"An error occurred in SignInView: {str(e)}")
            return Response({'error': 'Internal Server Error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SignUpView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            # Check if the login is already taken
            existing_user = User.objects.filter(login=request.data['login']).exists()
            if existing_user:
                return Response({'error': 'Login already taken. Please choose a different login.'}, status=400)


            user = serializer.save()

            token = jwt_encode_handler(
                {'userID': user.id, 'exp_time': int((datetime.now() + timedelta(days=1)).timestamp())})

            return Response({
                'token': str(token),
                'id': user.id,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        



class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    @action(detail=False, methods=['post'], url_path='send')
    def send_message(self, request):
        sender_id = request.data.get('sender_id')
        receiver_id = request.data.get('receiver_id')
        text = request.data.get('text')

        if not sender_id or not receiver_id or not text:
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({'error': 'Sender or Receiver not found.'}, status=status.HTTP_404_NOT_FOUND)

        user_message = Message.objects.create(sender=sender, receiver=receiver, text=text)

        bot_responses = [
            "Привет! Как твои дела?",
            "Я тут для тебя. Спрашивай что угодно!",
            "Спасибо за сообщение, чем могу помочь?",
        ]
        bot_message = Message.objects.create(
            sender=receiver, 
            receiver=sender,
            text=bot_responses[len(text) % len(bot_responses)],
            is_bot_response=True
        )

        return Response(
            {
                'user_message': MessageSerializer(user_message).data,
                'bot_message': MessageSerializer(bot_message).data,
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='history')
    def chat_history(self, request):
        sender_id = request.query_params.get('sender_id')
        receiver_id = request.query_params.get('receiver_id')

        if not sender_id or not receiver_id:
            return Response({'error': 'sender_id and receiver_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({'error': 'Sender or Receiver not found.'}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(
            sender__in=[sender, receiver],
            receiver__in=[sender, receiver]
        ).order_by('timestamp')

        return Response(MessageSerializer(messages, many=True).data, status=status.HTTP_200_OK)