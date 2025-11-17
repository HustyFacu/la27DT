from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .models import Cliente, Trabajo, Turnos, TrabajoVehiculo, Vehiculo, ConfiguracionWhatsApp
from django.db.models import Sum
from .utils import enviar_whatsapp, generar_mensaje_reserva, generar_mensaje_cancelacion, generar_mensaje_modificacion
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

            # 7. ✅ Guardar turno en sesión para confirmar
            request.session['turno_id'] = turno.id
            
            print("=" * 50)
            print("🎉 ¡TURNO GUARDADO EXITOSAMENTE!")
            print(f"Redirigiendo a confirmación...")
            print("=" * 50)

            # ✅ Redirigir a página de confirmación
            return redirect('reservas_app:confirmar_reserva')

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
        'occupied_slots_json': occupied_slots_json
    })


def confirmar_reserva(request):
    """
    Muestra resumen de la reserva y permite confirmar para enviar WhatsApp
    """
    turno_id = request.session.get('turno_id')
    if not turno_id:
        messages.error(request, 'No se encontró la reserva')
        return redirect('reservas_app:calendar_view')
    
    turno = get_object_or_404(Turnos, id=turno_id)
    
    if request.method == 'POST':
        # Marcar como confirmado
        turno.confirmado = True
        turno.save()
        
        # Obtener configuración de WhatsApp
        try:
            config = ConfiguracionWhatsApp.objects.filter(activo=True).first()
            if not config:
                messages.error(request, 'No hay configuración de WhatsApp activa. Contacta al administrador.')
                return redirect('reservas_app:calendar_view')
            
            # Generar mensaje con datos de la reserva
            mensaje = generar_mensaje_reserva(turno)
            
            # Usar el número del admin
            numero_destino = config.numero_whatsapp.replace('+', '').replace(' ', '')
            
            print("=" * 50)
            print("📱 ENVIANDO WHATSAPP:")
            print(f"Número configurado en admin: {config.numero_whatsapp}")
            print(f"Número destino limpio: {numero_destino}")
            print("=" * 50)
            
            # Generar URL de WhatsApp
            resultado = enviar_whatsapp(numero_destino, mensaje)
            
            if resultado['success']:
                turno.mensaje_enviado = True
                turno.save()
                
                # Limpiar sesión
                del request.session['turno_id']
                
                return render(request, 'reservas/reserva_success.html', {
                    'turno': turno,
                    'whatsapp_url': resultado['url'],
                    'mensaje': mensaje
                })
            else:
                messages.error(request, 'Error al generar el enlace de WhatsApp')
                
        except Exception as e:
            messages.error(request, f'Error al procesar: {str(e)}')
            print(f"ERROR en confirmar_reserva: {e}")
            import traceback
            traceback.print_exc()
    
    # Obtener información completa del turno
    trabajo_vehiculo = turno.trabajos_vehiculo.first()
    vehiculo = turno.cliente.vehiculos.first()
    
    return render(request, 'reservas/confirmar_reserva.html', {
        'turno': turno,
        'trabajo': trabajo_vehiculo.trabajo if trabajo_vehiculo else None,
        'vehiculo': vehiculo
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
                'fecha_iso': turno.fecha_turno.strftime('%Y-%m-%d'),
                'servicio': trabajo_vehiculo.trabajo.tipo_trabajo,
                'servicio_id': trabajo_vehiculo.trabajo.id,
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
def modificar_turno(request):
    """
    Vista para modificar un turno existente.
    Mantiene el mismo código único pero actualiza los datos.
    ✅ NUEVO: Envía WhatsApp al administrador notificando la modificación
    """
    codigo = request.POST.get('codigo', '').strip().upper()
    nueva_fecha_str = request.POST.get('fecha')
    nuevo_servicio_id = request.POST.get('tipo_servicio')
    nuevo_tipo_vehiculo = request.POST.get('tipo_vehiculo')
    nuevos_detalles = request.POST.get('detalles_trabajo', '')

    print("=" * 50)
    print("🔄 MODIFICANDO TURNO:")
    print(f"Código: {codigo}")
    print(f"Nueva Fecha: {nueva_fecha_str}")
    print(f"Nuevo Servicio ID: {nuevo_servicio_id}")
    print(f"Nuevo Tipo Vehículo: {nuevo_tipo_vehiculo}")
    print(f"Nuevos Detalles: {nuevos_detalles}")
    print("=" * 50)

    if not codigo:
        return JsonResponse({
            'success': False,
            'error': 'Código no proporcionado'
        }, status=400)

    try:
        # 1. Buscar el turno existente
        turno = Turnos.objects.select_related('cliente').prefetch_related('trabajos_vehiculo').get(
            codigo_unico=codigo
        )

        # 2. Si se proporciona nueva fecha, actualizarla
        if nueva_fecha_str:
            nueva_fecha_dt = datetime.strptime(nueva_fecha_str, '%Y-%m-%d %H:%M:%S')
            nueva_fecha_dt = timezone.make_aware(nueva_fecha_dt)
            turno.fecha_turno = nueva_fecha_dt
            print(f"✅ Nueva fecha: {nueva_fecha_dt}")

        # 3. Actualizar detalles del trabajo
        if nuevos_detalles:
            turno.descripcion_usuario = nuevos_detalles
            print(f"✅ Nuevos detalles: {nuevos_detalles}")

        turno.save()

        # 4. Si se cambió el servicio, actualizar TrabajoVehiculo
        if nuevo_servicio_id:
            nuevo_trabajo = Trabajo.objects.get(id=nuevo_servicio_id)
            trabajo_vehiculo = turno.trabajos_vehiculo.first()
            
            if trabajo_vehiculo:
                trabajo_vehiculo.trabajo = nuevo_trabajo
                trabajo_vehiculo.save()
                print(f"✅ Servicio actualizado a: {nuevo_trabajo}")
            else:
                TrabajoVehiculo.objects.create(
                    turno=turno,
                    trabajo=nuevo_trabajo
                )
                print(f"✅ Servicio creado: {nuevo_trabajo}")

        # 5. Si se cambió el tipo de vehículo, actualizar
        if nuevo_tipo_vehiculo:
            vehiculo = turno.cliente.vehiculos.first()
            if vehiculo:
                vehiculo.tipo_vehiculo = nuevo_tipo_vehiculo
                vehiculo.save()
                print(f"✅ Tipo de vehículo actualizado a: {nuevo_tipo_vehiculo}")
            else:
                Vehiculo.objects.create(
                    tipo_vehiculo=nuevo_tipo_vehiculo,
                    cliente=turno.cliente
                )
                print(f"✅ Vehículo creado: {nuevo_tipo_vehiculo}")

        # 🆕 6. ENVIAR WHATSAPP AL ADMINISTRADOR
        whatsapp_url = None
        try:
            config = ConfiguracionWhatsApp.objects.filter(activo=True).first()
            if config:
                mensaje = generar_mensaje_modificacion(turno)
                numero_destino = config.numero_whatsapp.replace('+', '').replace(' ', '')
                
                print("=" * 50)
                print("📱 ENVIANDO NOTIFICACIÓN DE MODIFICACIÓN POR WHATSAPP")
                print(f"Número destino: {numero_destino}")
                print("=" * 50)
                
                resultado = enviar_whatsapp(numero_destino, mensaje)
                
                if resultado['success']:
                    print("✅ WhatsApp de modificación enviado exitosamente")
                    whatsapp_url = resultado['url']
                else:
                    print(f"⚠️ No se pudo enviar WhatsApp: {resultado.get('error', 'Error desconocido')}")
            else:
                print("⚠️ No hay configuración de WhatsApp activa")
        except Exception as e:
            print(f"❌ Error al enviar WhatsApp: {e}")

        print("=" * 50)
        print("🎉 ¡TURNO MODIFICADO EXITOSAMENTE!")
        print(f"Código mantiene: {turno.codigo_unico}")
        print("=" * 50)

        return JsonResponse({
            'success': True,
            'message': 'Turno modificado exitosamente',
            'codigo': turno.codigo_unico,
            'whatsapp_url': whatsapp_url
        })

    except Turnos.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No se encontró ningún turno con ese código'
        }, status=404)
    except Trabajo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Servicio no válido'
        }, status=400)
    except Exception as e:
        print(f"ERROR en modificar_turno: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Error al modificar el turno: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def cancelar_turno(request):
    """
    Vista para cancelar un turno existente.
    ✅ NUEVO: Envía WhatsApp al administrador notificando la cancelación
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
        
        # 🆕 1. ENVIAR WHATSAPP ANTES DE ELIMINAR
        whatsapp_url = None
        try:
            config = ConfiguracionWhatsApp.objects.filter(activo=True).first()
            if config:
                mensaje = generar_mensaje_cancelacion(turno)
                numero_destino = config.numero_whatsapp.replace('+', '').replace(' ', '')
                
                print("=" * 50)
                print("📱 ENVIANDO NOTIFICACIÓN DE CANCELACIÓN POR WHATSAPP")
                print(f"Número destino: {numero_destino}")
                print("=" * 50)
                
                resultado = enviar_whatsapp(numero_destino, mensaje)
                
                if resultado['success']:
                    print("✅ WhatsApp de cancelación enviado exitosamente")
                    whatsapp_url = resultado['url']
                else:
                    print(f"⚠️ No se pudo enviar WhatsApp: {resultado.get('error', 'Error desconocido')}")
            else:
                print("⚠️ No hay configuración de WhatsApp activa")
        except Exception as e:
            print(f"❌ Error al enviar WhatsApp: {e}")
        
        # 2. AHORA SÍ ELIMINAR EL TURNO
        turno.delete()
        
        print("✅ Turno cancelado exitosamente")
        print("📊 El dashboard se actualizará al refrescar")
        print("=" * 50)

        return JsonResponse({
            'success': True,
            'message': 'Turno cancelado exitosamente',
            'whatsapp_url': whatsapp_url
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
    """
    hoy = timezone.now().date()
    mes_actual = hoy.month
    año_actual = hoy.year

    turnos_hoy = Turnos.objects.filter(fecha_turno__date=hoy).count()
    turnos_mes = Turnos.objects.filter(
        fecha_turno__month=mes_actual,
        fecha_turno__year=año_actual
    ).count()

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

    proximos_turnos = Turnos.objects.filter(
        fecha_turno__gte=hoy
    ).select_related('cliente').order_by('fecha_turno')[:10]

    context = {
        'turnos_hoy': turnos_hoy,
        'turnos_mes': turnos_mes,
        'ingresos_hoy': ingresos_hoy,
        'ingresos_mes': ingresos_mes,
        'turnos_max_dia': 12,
        'proximos_turnos': proximos_turnos,
        'labels_dias': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
        'ingresos_ultimos_dias': [10000, 12000, 8000, 15000, 20000, 18000, 22000],
        'servicios_labels': ['Lavado', 'Pulido', 'Cerámica', 'Interior', 'Motor'],
        'servicios_cantidades': [20, 15, 10, 8, 5],
        'vehiculos_labels': ['Auto', 'SUV', 'Camioneta', 'Moto'],
        'vehiculos_cantidades': [30, 12, 15, 3],
    }

    return render(request, 'dashboard.html', context)