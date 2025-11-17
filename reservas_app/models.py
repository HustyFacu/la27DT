from django.db import models
import random
import string


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
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio ($)")

    class Meta:
        verbose_name = "Trabajo"
        verbose_name_plural = "Trabajos"

    def __str__(self):
        return f"{self.tipo_trabajo} (${self.precio})"


class Turnos(models.Model):
    fecha_turno = models.DateTimeField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='turnos')
    descripcion_usuario = models.TextField(blank=True, null=True, verbose_name="Detalle del cliente")
    codigo_unico = models.CharField(max_length=12, unique=True, blank=True, editable=False)
    confirmado = models.BooleanField(default=False, verbose_name="Turno confirmado")  # ✅ NUEVO
    mensaje_enviado = models.BooleanField(default=False, verbose_name="WhatsApp enviado")  # ✅ NUEVO

    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            self.codigo_unico = self.generar_codigo_unico()
        super().save(*args, **kwargs)

    def generar_codigo_unico(self):
        while True:
            letras = ''.join(random.choices(string.ascii_uppercase, k=3))
            numeros = ''.join(random.choices(string.digits, k=3))
            codigo = f"LA27-{letras}{numeros}"
            if not Turnos.objects.filter(codigo_unico=codigo).exists():
                return codigo

    def __str__(self):
        return f"Turno de {self.cliente.nombre} el {self.fecha_turno.strftime('%d/%m/%Y %H:%M')} - Código: {self.codigo_unico}"

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['-fecha_turno']


class TrabajoVehiculo(models.Model):
    turno = models.ForeignKey(Turnos, on_delete=models.CASCADE, related_name='trabajos_vehiculo')
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.turno} - {self.trabajo}"


# ✅✅✅ ESTE ES EL MODELO QUE TE FALTABA ✅✅✅
class ConfiguracionWhatsApp(models.Model):
    numero_whatsapp = models.CharField(
        max_length=20, 
        help_text="Formato: +5493764123456 o 3764123456",
        verbose_name="Número de WhatsApp"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Configuración WhatsApp"
        verbose_name_plural = "Configuraciones WhatsApp"

    def __str__(self):
        return f"WhatsApp: {self.numero_whatsapp}"