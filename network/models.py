from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime

class User(AbstractUser):
    pass

class Posts(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    data = models.DateTimeField(default=datetime.datetime.now)
    texto = models.CharField(max_length=900)
    dono = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_postou")
    likes = models.ManyToManyField(User, related_name="like", default=None, blank=True)
    like_count = models.BigIntegerField(default="0")
    def __str__(self):
        return f"{self.texto}, postado por {self.dono}, dia {self.data}."
    @property
    def total_likes(self):
        return self.likes.count()


class Likes(models.Model):
    quem_deu_like = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_likou")
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name="post_likado")
    def __str__(self):
        return f"{self.quem_deu_like}, gostou do post {self.post}."


class Followers(models.Model):
    conta = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conta_atual") # so uma pessoa
    seguindo = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seguiu")