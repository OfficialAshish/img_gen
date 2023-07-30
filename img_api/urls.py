from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'img_api'

urlpatterns = [
    # path('',views.home,name="home"),
    path('', views.generateView,name='image-generate'),
    path('gallery/',views.galleryView ,name='image-gallery'),
    path('image/<int:id>', views.detailView,name='image-detail'),
    # path('media/images/<int:id>', views.detailView,name='image-detail'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

