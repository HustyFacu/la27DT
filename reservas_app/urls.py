from django.urls import path
from . import views

app_name = 'reservas_app'

urlpatterns = [
    path('', views.index, name='calendar_view'),
    path('buscar-turno/', views.buscar_turno, name='buscar_turno'),
    path('cancelar-turno/', views.cancelar_turno, name='cancelar_turno'),
    path('admin/logout/', views.logout_view, name='logout'),
]
