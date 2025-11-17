from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib.admin.sites import site
from django.contrib import admin
from .models import Cliente, Vehiculo, Marca, Trabajo, Turnos, TrabajoVehiculo, ConfiguracionWhatsApp


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
    list_display = ('cliente', 'fecha_turno', 'codigo_unico', 'confirmado', 'mensaje_enviado', 'get_descripcion_corta')
    list_filter = ('fecha_turno', 'confirmado', 'mensaje_enviado')
    search_fields = ('cliente__nombre', 'cliente__telefono', 'codigo_unico')
    readonly_fields = ('codigo_unico',)
    list_editable = ('confirmado',)

    def get_descripcion_corta(self, obj):
        """Muestra el detalle del cliente de forma limpia"""
        if obj.descripcion_usuario:
            if len(obj.descripcion_usuario) > 50:
                return obj.descripcion_usuario[:50] + '...'
            return obj.descripcion_usuario
        return '—'
    get_descripcion_corta.short_description = 'Detalle del cliente'


# ✅ NUEVO: Configuración WhatsApp
@admin.register(ConfiguracionWhatsApp)
class ConfiguracionWhatsAppAdmin(admin.ModelAdmin):
    list_display = ('numero_whatsapp', 'activo', 'fecha_actualizacion')
    list_editable = ('activo',)
    
    def has_add_permission(self, request):
        # Solo permite crear si no existe ninguna configuración
        return not ConfiguracionWhatsApp.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permite borrar configuraciones
        return False


# ================================
# 📊 DASHBOARD INDEX OVERRIDE - CORREGIDO
# ================================
def custom_admin_index(request):
    """
    Vista personalizada para el dashboard del admin - CON DATOS REALES
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

    # ✅ Métricas básicas REALES - USANDO RANGOS DE DATETIME
    inicio_hoy = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_hoy = now_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    turnos_hoy = Turnos.objects.filter(
        fecha_turno__gte=inicio_hoy,
        fecha_turno__lte=fin_hoy
    ).count()
    print(f"✅ Turnos HOY ({today}): {turnos_hoy}")

    inicio_mes = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    turnos_mes = Turnos.objects.filter(fecha_turno__gte=inicio_mes).count()
    print(f"✅ Turnos ESTE MES (desde {first_day_month}): {turnos_mes}")

    ingresos_hoy = (
        TrabajoVehiculo.objects.filter(
            turno__fecha_turno__gte=inicio_hoy,
            turno__fecha_turno__lte=fin_hoy
        ).aggregate(total=Sum("trabajo__precio"))["total"] or 0
    )
    print(f"💰 Ingresos HOY: ${ingresos_hoy}")

    ingresos_mes = (
        TrabajoVehiculo.objects.filter(
            turno__fecha_turno__gte=inicio_mes
        ).aggregate(total=Sum("trabajo__precio"))["total"] or 0
    )
    print(f"💰 Ingresos MES: ${ingresos_mes}")
    print("=" * 60)

    # ✅ Próximos turnos
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

    # 🆕 INGRESOS ÚLTIMOS 7 DÍAS (DATOS REALES)
    meses_es = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    dias_es = {
        0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
        4: 'viernes', 5: 'sábado', 6: 'domingo'
    }
    
    ingresos_dias_detalle = []
    for i in range(6, -1, -1):
        dia = today - timedelta(days=i)
        ingreso_dia = (
            TrabajoVehiculo.objects.filter(turno__fecha_turno__date=dia)
            .aggregate(total=Sum("trabajo__precio"))["total"] or 0
        )
        
        # Formatear fecha en español: "lunes 11/11"
        dia_semana = dias_es[dia.weekday()]
        label = f"{dia_semana.capitalize()} {dia.strftime('%d/%m')}"
        
        ingresos_dias_detalle.append((label, float(ingreso_dia)))
        print(f"💵 {label}: ${ingreso_dia}")

    # 🆕 SERVICIOS MÁS SOLICITADOS (ÚLTIMOS 30 DÍAS)
    servicios_populares = (
        TrabajoVehiculo.objects.filter(
            turno__fecha_turno__date__gte=today - timedelta(days=30)
        )
        .values('trabajo__tipo_trabajo')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:5]
    )

    print("=" * 60)
    print("🏆 TOP 5 SERVICIOS:")
    for idx, s in enumerate(servicios_populares, 1):
        print(f"   {idx}. {s['trabajo__tipo_trabajo']}: {s['cantidad']} veces")
    print("=" * 60)

    context = {
        **site.each_context(request),
        'title': 'Dashboard - LA27 Detailing',
        'site_title': site.site_title,
        'site_header': site.site_header,
        'site_url': site.site_url,
        'has_permission': site.has_permission(request),
        'available_apps': site.get_app_list(request),

        # ✅ Estadísticas principales
        "turnos_hoy": turnos_hoy,
        "turnos_mes": turnos_mes,
        "ingresos_hoy": ingresos_hoy,
        "ingresos_mes": ingresos_mes,
        "turnos_max_dia": 5,
        "proximos_turnos": proximos_turnos,

        # 🆕 NUEVOS DATOS PARA LISTAS
        "ingresos_dias_detalle": ingresos_dias_detalle,
        "servicios_populares": servicios_populares,
    }

    return render(request, "admin/index.html", context)


# Reemplazar el index del admin
admin.site.index = custom_admin_index
admin.site.site_header = "LA27 Detailing Admin"
admin.site.site_title = "LA27 Admin"
admin.site.index_title = "Dashboard"