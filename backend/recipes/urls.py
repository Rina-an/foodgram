from django.urls import path

from recipes import views

app_name = 'recipes'

urlpatterns = [
    path('s/<str:short_code>/',
         views.short_link_redirect,
         name='short_link'
         ),
]
