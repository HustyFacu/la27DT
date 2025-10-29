# reservas_app/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Cliente, Trabajos, Turnos, TrabajoVehiculo, Vehiculo
from django.shortcuts import render, get_object_or_404
from .models import Trabajos 


def reservar(request):
    trabajos = Trabajos.objects.all()
    precio=0

    if request.method == "POST":
        trabajo_id = request.POST.get("tipo_servicio")
        if trabajo_id:
            trabajo = Trabajos.objects.get(id=trabajo_id)
            precio = trabajos.precio

    return render(request, "tu_template.html", {"trabajos": trabajos, "precio": precio})






def calendar_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        tipo_servicio = request.POST.get('tipo_servicio')
        tipo_vehiculo = request.POST.get('tipo_vehiculo')  # 👈 nuevo
        detalles_trabajo = request.POST.get('detalles_trabajo')
        fecha_str = request.POST.get('fecha')

        # Validar campos obligatorios
        if not all([nombre, telefono, tipo_servicio, fecha_str, tipo_vehiculo]):
            messages.error(request, '⚠️ Todos los campos son obligatorios (incluido tipo de vehículo).')
            return redirect('calendar_view')

        try:
            # Convertir fecha
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            fecha_dt = timezone.make_aware(fecha_dt)

            # Crear cliente
            cliente = Cliente.objects.create(nombre=nombre, telefono=telefono)

            # Crear vehículo asociado al cliente
            vehiculo = Vehiculo.objects.create(
                tipo_vehiculo=tipo_vehiculo,
                cliente=cliente
            )

            # Crear trabajo
            trabajo = Trabajos.objects.create(
                descripcion_usuario=detalles_trabajo or "Sin detalles",
                tipo_trabajo=tipo_servicio
            )

            # Crear turno
            turno = Turnos.objects.create(fecha_turno=fecha_dt, cliente=cliente)

            # Relacionar turno con trabajo
            TrabajoVehiculo.objects.create(turno=turno, trabajo=trabajo, fecha_turno=fecha_dt)

            messages.success(request, f'✅ ¡Reserva creada con éxito para un {tipo_vehiculo}!')
            return redirect('calendar_view')

        except Exception as e:
            messages.error(request, f"❌ Error al guardar la reserva: {e}")
            print(f"ERROR: {e}")
            return redirect('calendar_view')

    return render(request, 'index.html')
