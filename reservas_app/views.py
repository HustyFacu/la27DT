# reservas_app/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Cliente, Trabajos, Turnos, TrabajoVehiculo

def calendar_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        tipo_servicio = request.POST.get('tipo_servicio')
        detalles_trabajo = request.POST.get('detalles_trabajo')
        fecha_str = request.POST.get('fecha')

        # Validar campos
        if not all([nombre, telefono, tipo_servicio, fecha_str]):
            messages.error(request, '⚠️ Todos los campos son obligatorios.')
            return redirect('calendar_view')

        try:
            # Convertir fecha a datetime
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            fecha_dt = timezone.make_aware(fecha_dt)

            # Crear cliente nuevo (no hay login)
            cliente = Cliente.objects.create(nombre=nombre, telefono=telefono)

            # Crear trabajo según el servicio elegido
            trabajo = Trabajos.objects.create(
                descripcion_usuario=detalles_trabajo or "Sin detalles",
                tipo_trabajo=tipo_servicio
            )

            # Crear turno asociado al cliente
            turno = Turnos.objects.create(fecha_turno=fecha_dt, cliente=cliente)

            # Relacionar turno con trabajo
            TrabajoVehiculo.objects.create(turno=turno, trabajo=trabajo, fecha_turno=fecha_dt)

            messages.success(request, '✅ ¡Reserva creada con éxito!')
            return redirect('calendar_view')

        except Exception as e:
            messages.error(request, f"❌ Error al guardar la reserva: {e}")
            print(f"ERROR: {e}")
            return redirect('calendar_view')

    # Renderizar la plantilla
    return render(request, 'index.html')
