from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Cliente, Trabajo, Turnos, TrabajoVehiculo, Vehiculo


def index(request):
    """
    Vista principal del sitio La 27 Detailing.
    Maneja tanto GET (mostrar formulario) como POST (guardar reserva).
    """
    
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        tipo_servicio_id = request.POST.get('tipo_servicio')  # Este es el ID del trabajo
        tipo_vehiculo = request.POST.get('tipo_vehiculo')
        detalles_trabajo = request.POST.get('detalles_trabajo', '')
        fecha_str = request.POST.get('fecha')

        # Imprimir en consola para debugging
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
            # 1. Convertir fecha a datetime con zona horaria
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

            # 4. Obtener el trabajo por ID
            try:
                trabajo = Trabajo.objects.get(id=tipo_servicio_id)
                print(f"✅ Trabajo encontrado: {trabajo}")
            except Trabajo.DoesNotExist:
                messages.error(request, '⚠️ El servicio seleccionado no existe.')
                trabajos = Trabajo.objects.all()
                return render(request, 'index.html', {'trabajos': trabajos})

            # 5. Actualizar descripción del trabajo si se proporcionó
            if detalles_trabajo:
                trabajo.descripcion_usuario = detalles_trabajo
                trabajo.save()
                print(f"✅ Descripción actualizada: {detalles_trabajo}")

            # 6. Crear turno
            turno = Turnos.objects.create(
                fecha_turno=fecha_dt,
                cliente=cliente
            )
            print(f"✅ Turno creado: {turno}")

            # 7. Crear TrabajoVehiculo (LA RELACIÓN CLAVE)
            trabajo_vehiculo = TrabajoVehiculo.objects.create(
                turno=turno,
                trabajo=trabajo
            )
            print(f"✅ TrabajoVehiculo creado: {trabajo_vehiculo}")
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

    # GET: Mostrar formulario con lista de trabajos
    trabajos = Trabajo.objects.all()
    return render(request, 'index.html', {'trabajos': trabajos})


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
        # Buscar el turno por código único
        turno = Turnos.objects.select_related('cliente').prefetch_related('trabajos_vehiculo__trabajo').get(
            codigo_unico=codigo
        )
        
        # Obtener el primer trabajo relacionado (asumiendo que hay al menos uno)
        trabajo_vehiculo = turno.trabajos_vehiculo.first()
        
        if not trabajo_vehiculo:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró información del servicio para este turno'
            }, status=404)
        
        # Obtener el vehículo del cliente para este turno
        vehiculo = turno.cliente.vehiculos.first()
        tipo_vehiculo = vehiculo.tipo_vehiculo if vehiculo else 'No especificado'
        
        # Preparar los datos para enviar
        data = {
            'success': True,
            'turno': {
                'codigo': turno.codigo_unico,
                'fecha': turno.fecha_turno.strftime('%d de %B %Y'),
                'hora': turno.fecha_turno.strftime('%H:%M'),
                'servicio': trabajo_vehiculo.trabajo.tipo_trabajo,
                'precio': str(trabajo_vehiculo.trabajo.precio),
                'detalles': trabajo_vehiculo.trabajo.descripcion_usuario or 'Sin detalles especificados',
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
        turno.delete()
        
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