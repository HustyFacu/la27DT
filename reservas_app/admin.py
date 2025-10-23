from django.contrib import admin
from .models import Cliente, Vehiculo, Marca, Trabajos, Turnos, TrabajoVehiculo

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono')
    search_fields = ('nombre', 'telefono')


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('tipo_vehiculo', 'modelo', 'dominio', 'cliente')
    list_filter = ('tipo_vehiculo',)
    search_fields = ('dominio', 'modelo', 'cliente__nombre')


@admin.register(Trabajos)
class TrabajosAdmin(admin.ModelAdmin):
    list_display = ('tipo_trabajo', 'descripcion_usuario')
    search_fields = ('tipo_trabajo', 'descripcion_usuario')


@admin.register(Turnos)
class TurnosAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha_turno')
    list_filter = ('fecha_turno',)
    search_fields = ('cliente__nombre', 'cliente__telefono')


# 💥 Aquí es donde agregamos todo lo interesante
@admin.register(TrabajoVehiculo)
class TrabajoVehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'get_cliente',
        'get_telefono',
        'get_tipo_vehiculo',
        'get_tipo_servicio',
        'fecha_turno',
    )
    list_filter = ('fecha_turno',)
    search_fields = ('turno__cliente__nombre', 'trabajo__tipo_trabajo')

    def get_cliente(self, obj):
        return obj.turno.cliente.nombre
    get_cliente.short_description = 'Cliente'

    def get_telefono(self, obj):
        return obj.turno.cliente.telefono
    get_telefono.short_description = 'Teléfono'

    def get_tipo_vehiculo(self, obj):
        vehiculo = obj.turno.cliente.vehiculos.first()
        return vehiculo.tipo_vehiculo.capitalize() if vehiculo else '—'
    get_tipo_vehiculo.short_description = 'Tipo Vehículo'

    def get_tipo_servicio(self, obj):
        return obj.trabajo.tipo_trabajo.replace('-', ' ').capitalize()
    get_tipo_servicio.short_description = 'Tipo Servicio'
