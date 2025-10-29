from django.contrib import admin
from .models import Cliente, Vehiculo, Marca, Trabajo, Turnos, TrabajoVehiculo

# -------------------
# Trabajo
# -------------------
@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ('tipo_trabajo', 'descripcion_usuario', 'precio')
    search_fields = ('tipo_trabajo', 'descripcion_usuario')

# -------------------
# Cliente
# -------------------
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono')
    search_fields = ('nombre', 'telefono')

# -------------------
# Marca
# -------------------
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

# -------------------
# Vehiculo
# -------------------
@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('tipo_vehiculo', 'modelo', 'dominio', 'cliente')
    list_filter = ('tipo_vehiculo',)
    search_fields = ('dominio', 'modelo', 'cliente__nombre')

# -------------------
# Turnos
# -------------------
@admin.register(Turnos)
class TurnosAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha_turno')
    list_filter = ('fecha_turno',)
    search_fields = ('cliente__nombre', 'cliente__telefono')

# -------------------
# TrabajoVehiculo
# -------------------
@admin.register(TrabajoVehiculo)
class TrabajoVehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'get_cliente',
        'get_telefono',
        'get_tipo_vehiculo',
        'get_tipo_servicio',
        'get_fecha_turno',
    )
    list_filter = ('turno__fecha_turno',)
    search_fields = ('turno__cliente__nombre', 'trabajo__tipo_trabajo')
    
    # CAMPOS EDITABLES - ESTO ES LO QUE FALTABA
    fields = ('turno', 'trabajo')
    
    # Facilita la búsqueda de turnos y trabajos en el formulario
    raw_id_fields = ('turno', 'trabajo')
    
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

    def get_fecha_turno(self, obj):
        return obj.turno.fecha_turno.strftime('%d/%m/%Y %H:%M')
    get_fecha_turno.short_description = 'Fecha Turno'