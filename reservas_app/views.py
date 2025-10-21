# reservas_app/views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Reserva
from django.contrib import messages
import calendar
from datetime import datetime, date, timedelta

class DayData:
    def __init__(self, date=None, is_today=False, has_reservation=False):
        self.date = date
        self.is_today = is_today
        self.has_reservation = has_reservation

def calendar_view(request):
    # Determinar año
    year_str = request.GET.get('year')
    if year_str:
        try:
            current_year = int(year_str)
        except ValueError:
            current_year = timezone.now().year
            messages.warning(request, 'El año proporcionado no es válido. Mostrando el año actual.')
    else:
        current_year = timezone.now().year

    # Determinar mes
    month_str = request.GET.get('month')
    if month_str:
        try:
            current_month = int(month_str)
            if not 1 <= current_month <= 12:
                current_month = timezone.now().month
                messages.warning(request, 'El mes proporcionado no es válido. Mostrando el mes actual.')
        except ValueError:
            current_month = timezone.now().month
            messages.warning(request, 'El mes proporcionado no es válido. Mostrando el mes actual.')
    else:
        current_month = timezone.now().month

    current_month_date = date(current_year, current_month, 1)

    # Mes siguiente y anterior
    next_month_date = current_month_date.replace(day=28) + timedelta(days=4)
    next_month_date = next_month_date.replace(day=1)
    prev_month_date = current_month_date - timedelta(days=1)
    prev_month_date = prev_month_date.replace(day=1)

    # Rango de fechas del mes (aware)
    start_of_month = timezone.make_aware(datetime(current_year, current_month, 1, 0, 0, 0))
    if current_month == 12:
        end_of_month = timezone.make_aware(datetime(current_year + 1, 1, 1, 0, 0, 0))
    else:
        end_of_month = timezone.make_aware(datetime(current_year, current_month + 1, 1, 0, 0, 0))
    end_of_month -= timedelta(microseconds=1)

    # Reservas del mes
    try:
        reservations_in_month = Reserva.objects.filter(
            fecha__gte=start_of_month,
            fecha__lte=end_of_month
        ).values_list('fecha__date', flat=True)
        reserved_dates = set(reservations_in_month)
    except Exception as e:
        messages.error(request, f"Error al cargar reservas: {e}. Puede que la base de datos no esté accesible.")
        reserved_dates = set()

    # Crear estructura del calendario
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(current_year, current_month)
    calendar_weeks_data = []
    today = timezone.localdate()

    for week in month_days:
        week_data = []
        for day_dt in week:
            if day_dt.month == current_month:
                is_today = (day_dt == today)
                has_reservation = (day_dt in reserved_dates)
                week_data.append(DayData(date=day_dt, is_today=is_today, has_reservation=has_reservation))
            else:
                week_data.append(DayData())
        calendar_weeks_data.append(week_data)

    # Fecha seleccionada
    selected_date_str = request.GET.get('selected_date')
    selected_date_obj = None
    if selected_date_str:
        try:
            selected_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.warning(request, 'La fecha seleccionada no tiene el formato correcto.')

    # Guardar reserva (POST)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        fecha_str = request.POST.get('fecha')

        print(f"DEBUG - Datos recibidos: nombre={nombre}, telefono={telefono}, fecha={fecha_str}")

        if not nombre or not telefono:
            messages.error(request, '⚠️ Todos los campos son obligatorios.')
        elif not fecha_str:
            messages.error(request, '⚠️ Debes elegir una fecha y una hora para el turno.')
        else:
            try:
                # Convertimos a datetime aware
                fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                fecha_dt = timezone.make_aware(fecha_dt)

                print(f"DEBUG - Fecha convertida: {fecha_dt}")

                # Validamos duplicado exacto fecha + hora
                if Reserva.objects.filter(fecha=fecha_dt).exists():
                    messages.error(request, '⛔ Ese turno ya está reservado a esa hora exacta.')
                else:
                    nueva_reserva = Reserva.objects.create(fecha=fecha_dt, nombre=nombre, telefono=telefono)
                    print(f"DEBUG - Reserva creada con ID: {nueva_reserva.id}")
                    messages.success(request, '✅ ¡Reserva guardada con éxito!')
                    return redirect(f"/?month={current_month_date.month}&year={current_month_date.year}")

            except ValueError as ve:
                print(f"DEBUG - Error ValueError: {ve}")
                messages.error(request, '⚠️ Fecha u hora inválida. Selecciona una fecha válida en formato YYYY-MM-DD HH:MM:SS.')
            except Exception as e:
                print(f"DEBUG - Error Exception: {e}")
                messages.error(request, f'Error al guardar la reserva: {e}')

    # Contexto para template
    context = {
        'current_month_name': calendar.month_name[current_month_date.month],
        'current_year': current_month_date.year,
        'current_month_date': current_month_date,
        'prev_month': prev_month_date,
        'next_month': next_month_date,
        'calendar_weeks': calendar_weeks_data,
        'selected_date': selected_date_obj,
    }
    return render(request, 'index.html', context)