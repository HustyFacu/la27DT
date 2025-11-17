from urllib.parse import quote
from django.utils import timezone


def enviar_whatsapp(numero_destino, mensaje):
    """
    Genera URL de WhatsApp para enviar mensaje
    
    Args:
        numero_destino: Número de WhatsApp (con o sin código de país)
        mensaje: Texto del mensaje a enviar
    
    Returns:
        dict: {'success': bool, 'url': str, 'message': str} o {'success': bool, 'error': str}
    """
    try:
        # Limpiar número (quitar espacios, guiones, paréntesis, +, etc.)
        numero_limpio = ''.join(filter(str.isdigit, numero_destino))
        
        # Validar que el número no esté vacío
        if not numero_limpio:
            return {
                'success': False,
                'error': 'Número de teléfono inválido'
            }
        
        # Si ya tiene código de país (54), no agregarlo de nuevo
        # Si no lo tiene, agregar +54 (Argentina)
        if not numero_limpio.startswith('54'):
            numero_limpio = '54' + numero_limpio
        
        # Codificar mensaje para URL
        mensaje_encoded = quote(mensaje)
        
        # Crear URL de WhatsApp Web/API
        url = f"https://api.whatsapp.com/send?phone={numero_limpio}&text={mensaje_encoded}"
        
        print("=" * 50)
        print("📱 URL DE WHATSAPP GENERADA:")
        print(f"Número destino: +{numero_limpio}")
        print(f"URL: {url[:100]}...")
        print("=" * 50)
        
        return {
            'success': True,
            'url': url,
            'message': 'URL generada correctamente'
        }
    
    except Exception as e:
        print(f"❌ ERROR en enviar_whatsapp: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def generar_mensaje_reserva(turno):
    """
    Genera el mensaje de confirmación de reserva para WhatsApp
    
    Args:
        turno: Objeto Turnos con la información de la reserva
    
    Returns:
        str: Mensaje formateado para WhatsApp
    """
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Convertir a hora local
    fecha_local = timezone.localtime(turno.fecha_turno)
    fecha_formateada = f"{fecha_local.day} de {meses[fecha_local.month]} de {fecha_local.year}"
    hora_formateada = fecha_local.strftime('%H:%M')
    
    # Obtener el servicio
    trabajo_vehiculo = turno.trabajos_vehiculo.first()
    servicio = trabajo_vehiculo.trabajo.tipo_trabajo if trabajo_vehiculo else "No especificado"
    
    # Obtener tipo de vehículo
    vehiculo = turno.cliente.vehiculos.first()
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
¡Gracias por tu reserva! Te esperamos.
━━━━━━━━━━━━━━━"""
    
    return mensaje


def generar_mensaje_cancelacion(turno):
    """
    Genera el mensaje de cancelación de turno para WhatsApp
    
    Args:
        turno: Objeto Turnos con la información del turno cancelado
    
    Returns:
        str: Mensaje formateado para WhatsApp
    """
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Convertir a hora local
    fecha_local = timezone.localtime(turno.fecha_turno)
    fecha_formateada = f"{fecha_local.day} de {meses[fecha_local.month]} de {fecha_local.year}"
    hora_formateada = fecha_local.strftime('%H:%M')
    
    # Obtener el servicio
    trabajo_vehiculo = turno.trabajos_vehiculo.first()
    servicio = trabajo_vehiculo.trabajo.tipo_trabajo if trabajo_vehiculo else "No especificado"
    
    # Obtener tipo de vehículo
    vehiculo = turno.cliente.vehiculos.first()
    tipo_vehiculo = vehiculo.tipo_vehiculo if vehiculo else "No especificado"
    
    mensaje = f"""❌ *Turno Cancelado*

Código: *{turno.codigo_unico}*

El cliente ha cancelado su turno:

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


def generar_mensaje_modificacion(turno):
    """
    Genera el mensaje de modificación de turno para WhatsApp
    
    Args:
        turno: Objeto Turnos con la información del turno modificado
    
    Returns:
        str: Mensaje formateado para WhatsApp
    """
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Convertir a hora local
    fecha_local = timezone.localtime(turno.fecha_turno)
    fecha_formateada = f"{fecha_local.day} de {meses[fecha_local.month]} de {fecha_local.year}"
    hora_formateada = fecha_local.strftime('%H:%M')
    
    # Obtener el servicio
    trabajo_vehiculo = turno.trabajos_vehiculo.first()
    servicio = trabajo_vehiculo.trabajo.tipo_trabajo if trabajo_vehiculo else "No especificado"
    
    # Obtener tipo de vehículo
    vehiculo = turno.cliente.vehiculos.first()
    tipo_vehiculo = vehiculo.tipo_vehiculo if vehiculo else "No especificado"
    
    mensaje = f"""🔄 *Turno Modificado*

Código: *{turno.codigo_unico}*

El cliente ha modificado su turno:

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