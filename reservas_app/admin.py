from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib.admin.sites import site
from django.contrib import admin
from .models import Cliente, Vehiculo, Marca, Trabajo, Turnos, TrabajoVehiculo


# -------------------
# Trabajo
# -------------------
@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ('tipo_trabajo', 'precio')
    search_fields = ('tipo_trabajo',)


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
    fields = ('turno', 'trabajo')
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
        return timezone.localtime(obj.turno.fecha_turno).strftime('%d/%m/%Y %H:%M')
    get_fecha_turno.short_description = 'Fecha Turno'


# -------------------
# Turnos
# -------------------
class TrabajoVehiculoInline(admin.TabularInline):
    model = TrabajoVehiculo
    extra = 1


@admin.register(Turnos)
class TurnosAdmin(admin.ModelAdmin):
    inlines = [TrabajoVehiculoInline]
    list_display = ('cliente', 'fecha_turno', 'codigo_unico', 'get_descripcion_corta')
    list_filter = ('fecha_turno',)
    search_fields = ('cliente__nombre', 'cliente__telefono', 'codigo_unico')
    readonly_fields = ('codigo_unico',)

    def get_descripcion_corta(self, obj):
        """Muestra el detalle del cliente de forma limpia"""
        if obj.descripcion_usuario:
            if len(obj.descripcion_usuario) > 50:
                return obj.descripcion_usuario[:50] + '...'
            return obj.descripcion_usuario
        return '—'
    get_descripcion_corta.short_description = 'Detalle del cliente'


# ================================
# 📊 DASHBOARD INDEX OVERRIDE
# ================================
def custom_admin_index(request):
    """
    Vista personalizada para el dashboard del admin
    """
    # Obtener hora local correctamente según settings.py
    now_utc = timezone.now()
    now_local = timezone.localtime(now_utc)
    today = now_local.date()
    first_day_month = today.replace(day=1)

    print("=" * 60)
    print(f"🕐 HORA ACTUAL DEL SERVIDOR (UTC): {now_utc}")
    print(f"🕐 HORA LOCAL (Argentina): {now_local}")
    print(f"📅 FECHA LOCAL: {today}")
    print("=" * 60)

    # Métricas básicas
    turnos_hoy = Turnos.objects.filter(fecha_turno__date=today).count()
    print(f"✅ Turnos HOY ({today}): {turnos_hoy}")

    turnos_mes = Turnos.objects.filter(fecha_turno__date__gte=first_day_month).count()
    print(f"✅ Turnos ESTE MES (desde {first_day_month}): {turnos_mes}")

    ingresos_hoy = (
        TrabajoVehiculo.objects.filter(turno__fecha_turno__date=today)
        .aggregate(total=Sum("trabajo__precio"))["total"] or 0
    )
    print(f"💰 Ingresos HOY: ${ingresos_hoy}")

    ingresos_mes = (
        TrabajoVehiculo.objects.filter(turno__fecha_turno__date__gte=first_day_month)
        .aggregate(total=Sum("trabajo__precio"))["total"] or 0
    )
    print(f"💰 Ingresos MES: ${ingresos_mes}")
    print("=" * 60)

    proximos_turnos = (
        Turnos.objects.filter(fecha_turno__gte=now_local)
        .select_related("cliente")
        .order_by("fecha_turno")[:10]
    )

    print(f"📋 Próximos {proximos_turnos.count()} turnos:")
    for t in proximos_turnos:
        fecha_local = timezone.localtime(t.fecha_turno)
        print(f"   - {t.cliente.nombre}: {fecha_local}")
    print("=" * 60)

    # 📊 Datos para gráficos
    ingresos_ultimos_dias = []
    labels_dias = []
    for i in range(6, -1, -1):
        dia = today - timedelta(days=i)
        ingreso_dia = (
            TrabajoVehiculo.objects.filter(turno__fecha_turno__date=dia)
            .aggregate(total=Sum("trabajo__precio"))["total"] or 0
        )
        ingresos_ultimos_dias.append(float(ingreso_dia))
        labels_dias.append(dia.strftime('%d/%m'))

    servicios_populares = (
        TrabajoVehiculo.objects.filter(
            turno__fecha_turno__date__gte=today - timedelta(days=30)
        )
        .values('trabajo__tipo_trabajo')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:5]
    )

    servicios_labels = [s['trabajo__tipo_trabajo'] for s in servicios_populares]
    servicios_cantidades = [s['cantidad'] for s in servicios_populares]

    vehiculos_stats = (
        Vehiculo.objects.values('tipo_vehiculo')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:5]
    )

    vehiculos_labels = [v['tipo_vehiculo'] or 'Sin especificar' for v in vehiculos_stats]
    vehiculos_cantidades = [v['cantidad'] for v in vehiculos_stats]

    context = {
        **site.each_context(request),
        'title': 'Dashboard - LA27 Detailing',
        'site_title': site.site_title,
        'site_header': site.site_header,
        'site_url': site.site_url,
        'has_permission': site.has_permission(request),
        'available_apps': site.get_app_list(request),

        "turnos_hoy": turnos_hoy,
        "turnos_mes": turnos_mes,
        "ingresos_hoy": ingresos_hoy,
        "ingresos_mes": ingresos_mes,
        "turnos_max_dia": 5,
        "proximos_turnos": proximos_turnos,

        "ingresos_ultimos_dias": ingresos_ultimos_dias,
        "labels_dias": labels_dias,
        "servicios_labels": servicios_labels,
        "servicios_cantidades": servicios_cantidades,
        "vehiculos_labels": vehiculos_labels,
        "vehiculos_cantidades": vehiculos_cantidades,
    }

    return render(request, "admin/dashboard.html", context)


# Reemplazar el index del admin
admin.site.index = custom_admin_index
admin.site.site_header = "LA27 Detailing Admin"
admin.site.site_title = "LA27 Admin"
admin.site.index_title = "Dashboard"
