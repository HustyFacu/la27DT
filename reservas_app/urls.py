from django.urls import path
from . import views

app_name = 'reservas_app'

urlpatterns = [
    path('', views.index, name='calendar_view'),
    path('confirmar/', views.confirmar_reserva, name='confirmar_reserva'),  # ✅ NUEVA
    path('buscar-turno/', views.buscar_turno, name='buscar_turno'),
    path('modificar-turno/', views.modificar_turno, name='modificar_turno'),
    path('cancelar-turno/', views.cancelar_turno, name='cancelar_turno'),
    path('dashboard/', views.dashboard, name='dashboard'),
]