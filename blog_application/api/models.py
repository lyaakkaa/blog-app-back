from django.db import models
from django.utils.timezone import now

class User(models.Model):
    person_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/')
    email = models.EmailField(unique=True)
    login = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)   
    favorite_users = models.ManyToManyField('self', symmetrical=False, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True) 
    location = models.CharField(max_length=255, null=True, blank=True)  
    activity = models.DateTimeField(null=True, blank=True)  

    def __str__(self):
        return self.person_name

class Topic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Post(models.Model):
    user = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    pub_date = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)
    commentary = models.TextField()
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    is_liked = models.BooleanField(default=False)
    like_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.commentary} by {self.user.person_name}"



class Message(models.Model):
    sender = models.ForeignKey('User', related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey('User', related_name='received_messages', on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(default=now)
    is_bot_response = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.person_name} -> {self.receiver.person_name}: {self.text}"
    


class Friend(models.Model):
    user1 = models.ForeignKey('User', related_name='friends_with_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey('User', related_name='friends_with_user2', on_delete=models.CASCADE)
    user1_name_for_user2 = models.CharField(max_length=100, null=True, blank=True)
    user2_name_for_user1 = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_friendship')
        ]

    def save(self, *args, **kwargs):
        # Ensure user1 has the smaller ID
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Friendship: {self.user1.person_name} & {self.user2.person_name}"
