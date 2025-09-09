# reservas_app/urls.py (Crea este archivo si no existe)
from django.urls import path
from . import views # Importa las vistas de tu propia aplicación

urlpatterns = [
    # La ruta vacía '' (que es la raíz del proyecto, porque la estamos incluyendo allí)
    # ahora apunta a la función 'calendar_view' de tu views.py.
    path('', views.calendar_view, name='calendar_view'),
]