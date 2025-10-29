from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=40)
    telefono = models.CharField(max_length=13)

    def __str__(self):
        return f"{self.nombre} ({self.telefono})"


class Marca(models.Model):
    nombre = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    tipo_vehiculo = models.CharField(max_length=20, blank=True, null=True)
    modelo = models.CharField(max_length=50, blank=True, null=True)
    dominio = models.CharField(max_length=10, blank=True, null=True)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='vehiculos')

    def __str__(self):
        return f"{self.dominio or 'sin dominio'} ({self.tipo_vehiculo or 'vehículo'})"


class Trabajo(models.Model):
    tipo_trabajo = models.CharField(max_length=100, verbose_name="Tipo de trabajo")
    descripcion_usuario = models.TextField(blank=True, null=True, verbose_name="Detalles")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio ($)")

    class Meta:
        verbose_name = "Trabajo"
        verbose_name_plural = "Trabajos"

    def __str__(self):
        return f"{self.tipo_trabajo} (${self.precio})"


class Turnos(models.Model):
    fecha_turno = models.DateTimeField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='turnos')

    def __str__(self):
        return f"Turno de {self.cliente.nombre} el {self.fecha_turno.strftime('%d/%m/%Y %H:%M')}"


class TrabajoVehiculo(models.Model):
    turno = models.ForeignKey(Turnos, on_delete=models.CASCADE)
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.turno} - {self.trabajo}"
