from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .models import Cliente, Trabajo, Turnos, TrabajoVehiculo, Vehiculo
from django.db.models import Sum
import json


def index(request):
    """
    Vista principal del sitio La 27 Detailing.
    Maneja tanto GET (mostrar formulario) como POST (guardar reserva).
    """

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        tipo_servicio_id = request.POST.get('tipo_servicio')
        tipo_vehiculo = request.POST.get('tipo_vehiculo')
        detalles_trabajo = request.POST.get('detalles_trabajo', '')
        fecha_str = request.POST.get('fecha')

        print("=" * 50)
        print("📋 DATOS RECIBIDOS DEL FORMULARIO:")
        print(f"Nombre: {nombre}")
        print(f"Teléfono: {telefono}")
        print(f"Tipo Servicio ID: {tipo_servicio_id}")
        print(f"Tipo Vehículo: {tipo_vehiculo}")
        print(f"Detalles: {detalles_trabajo}")
        print(f"Fecha: {fecha_str}")
        print("=" * 50)

        # Validar campos obligatorios
        if not all([nombre, telefono, tipo_servicio_id, fecha_str, tipo_vehiculo]):
            messages.error(request, '⚠️ Todos los campos son obligatorios.')
            trabajos = Trabajo.objects.all()
            return render(request, 'index.html', {'trabajos': trabajos})

        try:
            # 1. Convertir fecha
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            fecha_dt = timezone.make_aware(fecha_dt)
            print(f"✅ Fecha procesada: {fecha_dt}")

            # 2. Obtener o crear cliente
            cliente, created = Cliente.objects.get_or_create(
                telefono=telefono,
                defaults={'nombre': nombre}
            )
            if not created and cliente.nombre != nombre:
                cliente.nombre = nombre
                cliente.save()
            print(f"✅ Cliente: {cliente} (Creado: {created})")

            # 3. Crear vehículo
            vehiculo = Vehiculo.objects.create(
                tipo_vehiculo=tipo_vehiculo,
                cliente=cliente
            )
            print(f"✅ Vehículo creado: {vehiculo}")

            # 4. Obtener el trabajo
            trabajo = Trabajo.objects.get(id=tipo_servicio_id)
            print(f"✅ Trabajo encontrado: {trabajo}")

            # 5. Crear turno con detalles del usuario
            turno = Turnos.objects.create(
                fecha_turno=fecha_dt,
                cliente=cliente,
                descripcion_usuario=detalles_trabajo
            )
            print(f"✅ Turno creado con código: {turno.codigo_unico}")

            # 6. Crear relación trabajo-turno
            trabajo_vehiculo = TrabajoVehiculo.objects.create(
                turno=turno,
                trabajo=trabajo
            )
            print(f"✅ TrabajoVehiculo creado: {trabajo_vehiculo}")
            print("=" * 50)
            print("🎉 ¡TURNO GUARDADO EXITOSAMENTE EN LA BASE DE DATOS!")
            print(f"📊 El dashboard mostrará este turno al refrescar")
            print("=" * 50)

            messages.success(request, f'✅ ¡Reserva confirmada! Tu código es: {turno.codigo_unico}')
            return redirect('reservas_app:calendar_view')

        except ValueError as e:
            messages.error(request, f"❌ Error en el formato de fecha: {e}")
            print(f"ERROR ValueError: {e}")
        except Exception as e:
            messages.error(request, f"❌ Error al guardar la reserva: {e}")
            print(f"ERROR Exception: {e}")
            import traceback
            traceback.print_exc()

    # GET - Cargar turnos ocupados desde la BD para el JavaScript
    trabajos = Trabajo.objects.all()
    
    # ✨ Obtener todos los turnos futuros
    turnos_futuros = Turnos.objects.filter(
        fecha_turno__gte=timezone.now()
    ).select_related('cliente')
    
    # ✨ Organizar turnos por fecha para el calendario JavaScript
    occupied_slots = {}
    for turno in turnos_futuros:
        fecha_local = timezone.localtime(turno.fecha_turno)
        fecha_str = fecha_local.strftime('%Y-%m-%d')
        hora_str = fecha_local.strftime('%H:%M')
        
        if fecha_str not in occupied_slots:
            occupied_slots[fecha_str] = []
        
        occupied_slots[fecha_str].append(hora_str)
    
    # ✨ Convertir a JSON para JavaScript
    occupied_slots_json = json.dumps(occupied_slots)
    
    return render(request, 'index.html', {
        'trabajos': trabajos,
        'occupied_slots_json': occupied_slots_json  # ✨ Pasar turnos reales al frontend
    })


@require_http_methods(["GET"])
def buscar_turno(request):
    """
    Vista para buscar un turno por código único.
    Retorna los datos del turno en formato JSON.
    """
    codigo = request.GET.get('codigo', '').strip().upper()

    if not codigo:
        return JsonResponse({
            'success': False,
            'error': 'Código no proporcionado'
        }, status=400)

    try:
        turno = Turnos.objects.select_related('cliente').prefetch_related('trabajos_vehiculo__trabajo').get(
            codigo_unico=codigo
        )

        trabajo_vehiculo = turno.trabajos_vehiculo.first()
        if not trabajo_vehiculo:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró información del servicio para este turno'
            }, status=404)

        vehiculo = turno.cliente.vehiculos.first()
        tipo_vehiculo = vehiculo.tipo_vehiculo if vehiculo else 'No especificado'

        data = {
            'success': True,
            'turno': {
                'codigo': turno.codigo_unico,
                'fecha': turno.fecha_turno.strftime('%d de %B %Y'),
                'hora': turno.fecha_turno.strftime('%H:%M'),
                'servicio': trabajo_vehiculo.trabajo.tipo_trabajo,
                'precio': str(trabajo_vehiculo.trabajo.precio),
                'detalles': turno.descripcion_usuario or 'Sin detalles especificados',
                'vehiculo': tipo_vehiculo,
                'nombre': turno.cliente.nombre,
                'telefono': turno.cliente.telefono,
                'turno_id': turno.id
            }
        }

        return JsonResponse(data)

    except Turnos.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No se encontró ningún turno con ese código'
        }, status=404)
    except Exception as e:
        print(f"ERROR en buscar_turno: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Error al buscar el turno'
        }, status=500)


@require_http_methods(["POST"])
def cancelar_turno(request):
    """
    Vista para cancelar un turno existente.
    """
    codigo = request.POST.get('codigo', '').strip().upper()

    if not codigo:
        return JsonResponse({
            'success': False,
            'error': 'Código no proporcionado'
        }, status=400)

    try:
        turno = Turnos.objects.get(codigo_unico=codigo)
        
        print("=" * 50)
        print(f"🗑️ CANCELANDO TURNO: {turno.codigo_unico}")
        print(f"Cliente: {turno.cliente.nombre}")
        print(f"Fecha: {turno.fecha_turno}")
        print("=" * 50)
        
        turno.delete()
        
        print("✅ Turno cancelado exitosamente")
        print("📊 El dashboard se actualizará al refrescar")
        print("=" * 50)

        return JsonResponse({
            'success': True,
            'message': 'Turno cancelado exitosamente'
        })

    except Turnos.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No se encontró ningún turno con ese código'
        }, status=404)
    except Exception as e:
        print(f"ERROR en cancelar_turno: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error al cancelar el turno'
        }, status=500)



@staff_member_required
def dashboard(request):
    """
    Dashboard administrativo - muestra estadísticas actualizadas.
    Se refresca automáticamente al recargar la página o usar el botón "Actualizar".
    """
    hoy = timezone.now().date()
    mes_actual = hoy.month
    año_actual = hoy.year

    # 📅 Cantidad de turnos
    turnos_hoy = Turnos.objects.filter(fecha_turno__date=hoy).count()
    turnos_mes = Turnos.objects.filter(
        fecha_turno__month=mes_actual,
        fecha_turno__year=año_actual
    ).count()

    # 💰 Ingresos (sumando precios de los trabajos asociados)
    ingresos_hoy = (
        TrabajoVehiculo.objects.filter(turno__fecha_turno__date=hoy)
        .aggregate(total=Sum('trabajo__precio'))['total'] or 0
    )
    ingresos_mes = (
        TrabajoVehiculo.objects.filter(
            turno__fecha_turno__month=mes_actual,
            turno__fecha_turno__year=año_actual
        )
        .aggregate(total=Sum('trabajo__precio'))['total'] or 0
    )

    # 📆 Próximos turnos (para la tabla)
    proximos_turnos = Turnos.objects.filter(
        fecha_turno__gte=hoy
    ).select_related('cliente').order_by('fecha_turno')[:10]

    # Contexto para el template
    context = {
        'turnos_hoy': turnos_hoy,
        'turnos_mes': turnos_mes,
        'ingresos_hoy': ingresos_hoy,
        'ingresos_mes': ingresos_mes,
        'turnos_max_dia': 12,
        'proximos_turnos': proximos_turnos,
        # Datos de ejemplo para los gráficos
        'labels_dias': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
        'ingresos_ultimos_dias': [10000, 12000, 8000, 15000, 20000, 18000, 22000],
        'servicios_labels': ['Lavado', 'Pulido', 'Cerámica', 'Interior', 'Motor'],
        'servicios_cantidades': [20, 15, 10, 8, 5],
        'vehiculos_labels': ['Auto', 'SUV', 'Camioneta', 'Moto'],
        'vehiculos_cantidades': [30, 12, 15, 3],
    }

    return render(request, 'dashboard.html', context)