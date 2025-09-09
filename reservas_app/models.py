# reservas_app/models.py
from django.db import models

class Reserva(models.Model):
    fecha = models.DateTimeField(verbose_name="Fecha y Hora de la Reserva")
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        # Asegúrate de importar timezone si no lo has hecho en views.py
        # o de usar un formato simple que no necesite timezone aquí si no quieres
        return f"Reserva de {self.nombre} ({self.telefono}) para {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['fecha'] # Ordenar por fecha por defecto