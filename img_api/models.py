from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class GeneratedImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    text = models.CharField(max_length=250,blank=True,null=True)
    image = models.ImageField(upload_to='images')
    created_at = models.DateTimeField(auto_now_add=True)

    # image_url = models.URLField(unique=True)
    def get_absolute_url(self):
        return reverse('img_api:image-detail', kwargs={"id": self.id})
