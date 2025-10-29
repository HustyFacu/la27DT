from django.urls import path
from . import views

app_name = 'reservas_app'

urlpatterns = [
    path('', views.index, name='calendar_view'),
]
