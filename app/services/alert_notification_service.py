# app/services/alert_notification_service.py
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid 

from sqlalchemy.orm import Session 

# Importar operaciones CRUD
from app.crud.crud_alerta import alerta_crud
from app.crud.crud_user import user_crud # Para registrar quién gestionó la alerta
from app.crud.crud_bus import bus_crud # Para obtener detalles del bus para notificación
from app.crud.crud_conductor import conductor_crud # Para obtener detalles del conductor para notificación

# Importar modelos
from app.models_db.cloud_database_models import Alerta, Usuario, Bus, Conductor 

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# --- Módulos de Notificación (Simulados por ahora) ---
# En un sistema real, aquí importarías librerías para enviar SMS (Twilio), emails (SendGrid), etc.
class MockNotifier:
    def send_email(self, to_email: str, subject: str, body: str):
        logger.info(f"[NOTIFICACIÓN - EMAIL SIMULADO]: A '{to_email}' - Asunto: '{subject}' - Cuerpo: '{body[:50]}...'")

    def send_sms(self, to_phone: str, message: str):
        logger.info(f"[NOTIFICACIÓN - SMS SIMULADO]: A '{to_phone}' - Mensaje: '{message[:50]}...'")

    def send_dashboard_push(self, user_id: uuid.UUID, message: str):
        logger.info(f"[NOTIFICACIÓN - DASHBOARD PUSH SIMULADO]: A Usuario '{user_id}' - Mensaje: '{message[:50]}...'")

mock_notifier = MockNotifier()
# -----------------------------------------------------

class AlertNotificationService:
    """
    Capa de servicio para gestionar alertas y enviar notificaciones.
    Recibe alertas del EventProcessingService y las hace persistentes.
    También gestiona el ciclo de vida y las notificaciones de las alertas.
    """

    def create_alert(self, db: Session, alert_data: Dict[str, Any]) -> Optional[Alerta]:
        """
        Crea una nueva alerta en la base de datos central.
        Este método es llamado por el EventProcessingService cuando un evento dispara una alerta.
        
        Args:
            db (Session): Sesión de la base de datos.
            alert_data (Dict[str, Any]): Datos de la alerta a crear.
        
        Returns:
            Optional[Alerta]: El objeto Alerta creado, o None si falla.
        """
        logger.info(f"Intentando crear una nueva alerta: {alert_data.get('tipo_alerta')}")

        # Validaciones de FK (id_bus, id_conductor, id_evento, id_sesion_conduccion)
        bus_id = alert_data.get('id_bus')
        if bus_id and not bus_crud.get(db, bus_id):
            logger.warning(f"Fallo al crear alerta: Bus ID '{bus_id}' no encontrado.")
            return None
        
        conductor_id = alert_data.get('id_conductor')
        if conductor_id and not conductor_crud.get(db, conductor_id):
            logger.warning(f"Fallo al crear alerta: Conductor ID '{conductor_id}' no encontrado.")
            return None
        
        # Las validaciones para id_evento y id_sesion_conduccion pueden ser más flexibles
        # si se permite que una alerta exista sin un evento o sesión directa por fallos.
        
        try:
            new_alert = alerta_crud.create(db, alert_data)
            logger.info(f"Alerta '{new_alert.tipo_alerta}' (ID: {new_alert.id}) creada exitosamente.")
            
            # Opcional: Enviar notificación inmediatamente después de crear la alerta
            # self.send_alert_notification(db, new_alert)
            
            return new_alert
        except Exception as e:
            logger.error(f"Error creando alerta: {e}", exc_info=True)
            db.rollback()
            return None

    def update_alert_status(self, db: Session, alert_id: uuid.UUID, updates: Dict[str, Any], gestionada_por_usuario_id: Optional[uuid.UUID] = None) -> Optional[Alerta]:
        """
        Actualiza el estado y los detalles de gestión de una alerta.
        Esto sería llamado desde el Dashboard por un usuario supervisor.

        Args:
            db (Session): Sesión de la base de datos.
            alert_id (uuid.UUID): ID de la alerta a actualizar.
            updates (Dict[str, Any]): Diccionario con los campos a actualizar (ej. 'estado_alerta', 'tipo_gestion', 'comentarios_gestion').
            gestionada_por_usuario_id (Optional[uuid.UUID]): ID del usuario que gestionó la alerta.
        
        Returns:
            Optional[Alerta]: El objeto Alerta actualizado, o None si falla.
        """
        logger.info(f"Intentando actualizar alerta ID: {alert_id}")
        alert_existente: Optional[Alerta] = alerta_crud.get(db, alert_id)
        if not alert_existente:
            logger.warning(f"No se puede actualizar: Alerta con ID '{alert_id}' no encontrada.")
            return None
        
        # Registrar quién gestionó la alerta y cuándo
        if gestionada_por_usuario_id:
            usuario_gestor: Optional[Usuario] = user_crud.get(db, gestionada_por_usuario_id)
            if not usuario_gestor:
                logger.warning(f"Usuario gestor ID '{gestionada_por_usuario_id}' no encontrado. No se registra gestor.")
                # No se devuelve None, se continúa con la actualización sin asignar gestor.
            else:
                updates['gestionada_por_id_usuario'] = gestionada_por_usuario_id
                updates['fecha_gestion'] = datetime.utcnow() # Registrar fecha de gestión

        try:
            updated_alert = alerta_crud.update(db, alert_existente, updates)
            logger.info(f"Alerta ID '{alert_id}' actualizada exitosamente. Estado: {updated_alert.estado_alerta}")
            return updated_alert
        except Exception as e:
            logger.error(f"Error actualizando alerta ID '{alert_id}': {e}", exc_info=True)
            db.rollback()
            return None

    def send_alert_notification(self, db: Session, alert: Alerta):
        """
        Envía notificaciones para una alerta específica a través de los canales configurados.
        Este método es conceptual y dependerá de tus integraciones reales (Twilio, SendGrid, etc.).
        """
        logger.info(f"Preparando notificación para alerta ID: {alert.id} ({alert.tipo_alerta})")

        # Obtener detalles adicionales para la notificación (ej. nombre del conductor, placa del bus)
        bus: Optional[Bus] = bus_crud.get(db, alert.id_bus)
        conductor: Optional[Conductor] = conductor_crud.get(db, alert.id_conductor)

        notification_subject = f"ALERTA CRÍTICA: {alert.tipo_alerta} en Bus {bus.placa if bus else 'Desconocido'}"
        notification_body = (
            f"Alerta: {alert.tipo_alerta}\n"
            f"Descripción: {alert.descripcion}\n"
            f"Hora: {alert.timestamp_alerta.isoformat()}\n"
            f"Bus: {bus.placa if bus else 'N/A'} ({bus.numero_interno if bus else 'N/A'})\n"
            f"Conductor: {conductor.nombre_completo if conductor else 'N/A'} ({conductor.cedula if conductor else 'N/A'})\n"
            f"Nivel de Criticidad: {alert.nivel_criticidad}\n"
            f"Estado: {alert.estado_alerta}\n"
            f"ID de Alerta: {alert.id}"
            # Aquí podrías añadir enlaces a videoclips/snapshots si el evento lo tiene
            # f"Evidencia: {alert.evento.snapshot_url if alert.evento and alert.evento.snapshot_url else 'N/A'}"
        )

        # Asumimos que los canales de notificación están en la alerta o en la configuración global
        # Por ahora, simulamos el envío a un correo de ejemplo.
        
        # Enviar email
        mock_notifier.send_email(
            to_email="supervisores@tuempresa.com", # <<<<< CAMBIA ESTO POR UN EMAIL REAL DE SUPERVISIÓN
            subject=notification_subject,
            body=notification_body
        )
        
        # Enviar SMS (si tuvieras números de teléfono de supervisores)
        # mock_notifier.send_sms(
        #     to_phone="+573001234567", # <<<<< CAMBIA POR NÚMERO REAL
        #     message=f"Alerta: {alert.tipo_alerta} en Bus {bus.placa if bus else 'N/A'} con {conductor.nombre_completo if conductor else 'N/A'}"
        # )

        # Enviar notificación push al Dashboard (conceptual)
        # mock_notifier.send_dashboard_push(
        #     user_id=uuid.UUID("UUID_DEL_ADMINISTRADOR_PRINCIPAL"), # ID de un usuario administrador
        #     message=f"Nueva Alerta: {alert.tipo_alerta} - Bus {bus.placa if bus else 'N/A'}"
        # )

        logger.info(f"Notificación de alerta ID '{alert.id}' enviada a canales configurados.")

    def get_alert_details(self, db: Session, alert_id: uuid.UUID) -> Optional[Alerta]:
        """
        Recupera los detalles de una alerta específica por su ID.
        """
        logger.info(f"Obteniendo detalles para la alerta ID: {alert_id}")
        alert = alerta_crud.get(db, alert_id)
        # Opcional: Cargar también el Evento asociado si se necesita su URL de evidencia
        # if alert and alert.id_evento:
        #     from app.crud.crud_evento import evento_crud
        #     alert.evento_asociado = evento_crud.get(db, alert.id_evento) # Añadir como atributo al objeto Alerta
        if not alert:
            logger.warning(f"Alerta con ID '{alert_id}' no encontrada.")
        return alert

    def get_all_alerts(self, db: Session, skip: int = 0, limit: int = 100, 
                       status: Optional[str] = None, alert_type: Optional[str] = None) -> List[Alerta]:
        """
        Recupera una lista de todas las alertas con paginación y filtrado opcional por estado y tipo.
        """
        logger.info(f"Obteniendo alertas (skip={skip}, limit={limit}, status={status}, type={alert_type}).")
        return alerta_crud.get_alerts_by_type_and_status(db, tipo_alerta=alert_type, estado_alerta=status, skip=skip, limit=limit)
    
    def get_active_alerts_api(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alerta]:
        """
        Recupera una lista de alertas actualmente activas para mostrar en el Dashboard.
        """
        logger.info(f"Obteniendo alertas activas (skip={skip}, limit={limit}).")
        return alerta_crud.get_active_alerts(db, skip=skip, limit=limit)

# Crea una instancia de AlertNotificationService para ser utilizada por los endpoints API.
alert_notification_service = AlertNotificationService()