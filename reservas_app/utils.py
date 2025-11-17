from urllib.parse import quote
from django.utils import timezone
from reservas_app.models import Vehiculo  # IMPORTANTE


def enviar_whatsapp(numero_destino, mensaje):
    try:
        numero_limpio = ''.join(filter(str.isdigit, numero_destino))

        if not numero_limpio:
            return {'success': False, 'error': 'Número inválido'}

        if not numero_limpio.startswith("54"):
            numero_limpio = "54" + numero_limpio

        mensaje_encoded = quote(mensaje)
        url = f"https://api.whatsapp.com/send?phone={numero_limpio}&text={mensaje_encoded}"

        print("=" * 50)
        print("📱 URL DE WHATSAPP GENERADA:")
        print(f"Número destino: +{numero_limpio}")
        print(f"URL: {url[:100]}...")
        print("=" * 50)

        return {'success': True, 'url': url, 'message': 'URL generada correctamente'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


# ============================================================
#   🔥 FUNCIÓN CENTRAL PARA TOMAR EL VEHÍCULO CORRECTO 🔥
# ============================================================

def obtener_vehiculo_del_turno(turno):
    """
    Obtiene el vehículo asociado al turno de manera correcta.
    """
    return (
        Vehiculo.objects
        .filter(cliente=turno.cliente)
        .order_by("-id")  # Toma el último creado (el del turno)
        .first()
    )


# ============================================================
#   🔥 MENSAJE DE RESERVA
# ============================================================

def generar_mensaje_reserva(turno):

    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    fecha_local = timezone.localtime(turno.fecha_turno)
    fecha_formateada = f"{fecha_local.day} de {meses[fecha_local.month]} de {fecha_local.year}"
    hora_formateada = fecha_local.strftime("%H:%M")

    trabajo_vehiculo = turno.trabajos_vehiculo.first()
    servicio = trabajo_vehiculo.trabajo.tipo_trabajo if trabajo_vehiculo else "No especificado"

    # 🚘 OBTENER VEHÍCULO CORRECTO
    vehiculo = obtener_vehiculo_del_turno(turno)
    tipo_vehiculo = vehiculo.tipo_vehiculo if vehiculo else "No especificado"

    mensaje = f"""✅ *¡Reserva confirmada!*

Tu código es: *{turno.codigo_unico}*

📋 *Resumen de tu reserva:*

📅 *Fecha:* {fecha_formateada}
🕐 *Hora:* {hora_formateada}
🔧 *Servicio:* {servicio}
🚗 *Vehículo:* {tipo_vehiculo}
📝 *Detalles:* {turno.descripcion_usuario or 'No especificado'}
👤 *Nombre:* {turno.cliente.nombre}
📞 *Teléfono:* {turno.cliente.telefono}

━━━━━━━━━━━━━━━
🚙 *LA27 Detailing*
¡Gracias por tu reserva!
━━━━━━━━━━━━━━━"""

    return mensaje


# ============================================================
#   🔥 MENSAJE CANCELACIÓN
# ============================================================

def generar_mensaje_cancelacion(turno):
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    fecha_local = timezone.localtime(turno.fecha_turno)
    fecha_formateada = f"{fecha_local.day} de {meses[fecha_local.month]} de {fecha_local.year}"
    hora_formateada = fecha_local.strftime("%H:%M")

    trabajo_vehiculo = turno.trabajos_vehiculo.first()
    servicio = trabajo_vehiculo.trabajo.tipo_trabajo if trabajo_vehiculo else "No especificado"

    # 🚘 OBTENER VEHÍCULO CORRECTO
    vehiculo = obtener_vehiculo_del_turno(turno)
    tipo_vehiculo = vehiculo.tipo_vehiculo if vehiculo else "No especificado"

    mensaje = f"""❌ *Turno Cancelado*

Código: *{turno.codigo_unico}*

📅 *Fecha:* {fecha_formateada}
🕐 *Hora:* {hora_formateada}
🔧 *Servicio:* {servicio}
🚗 *Vehículo:* {tipo_vehiculo}
👤 *Cliente:* {turno.cliente.nombre}
📞 *Teléfono:* {turno.cliente.telefono}

━━━━━━━━━━━━━━━
🚙 *LA27 Detailing*
Turno cancelado por el cliente.
━━━━━━━━━━━━━━━"""

    return mensaje


# ============================================================
#   🔥 MENSAJE MODIFICACIÓN
# ============================================================

def generar_mensaje_modificacion(turno):

    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    fecha_local = timezone.localtime(turno.fecha_turno)
    fecha_formateada = f"{fecha_local.day} de {meses[fecha_local.month]} de {fecha_local.year}"
    hora_formateada = fecha_local.strftime("%H:%M")

    trabajo_vehiculo = turno.trabajos_vehiculo.first()
    servicio = trabajo_vehiculo.trabajo.tipo_trabajo if trabajo_vehiculo else "No especificado"

    # 🚘 OBTENER VEHÍCULO CORRECTO
    vehiculo = obtener_vehiculo_del_turno(turno)
    tipo_vehiculo = vehiculo.tipo_vehiculo if vehiculo else "No especificado"

    mensaje = f"""🔄 *Turno Modificado*

Código: *{turno.codigo_unico}*

📋 *NUEVOS DATOS:*

📅 *Fecha:* {fecha_formateada}
🕐 *Hora:* {hora_formateada}
🔧 *Servicio:* {servicio}
🚗 *Vehículo:* {tipo_vehiculo}
📝 *Detalles:* {turno.descripcion_usuario or 'No especificado'}
👤 *Cliente:* {turno.cliente.nombre}
📞 *Teléfono:* {turno.cliente.telefono}

━━━━━━━━━━━━━━━
🚙 *LA27 Detailing*
Turno actualizado exitosamente.
━━━━━━━━━━━━━━━"""

    return mensaje
