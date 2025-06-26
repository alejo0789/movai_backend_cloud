# app/services/event_processing_service.py
import logging
from datetime import datetime, timedelta 
from typing import Optional, Dict, Any, List
import uuid 

from sqlalchemy.orm import Session 

# Importar operaciones CRUD
from app.crud.crud_evento import evento_crud
from app.crud.crud_alerta import alerta_crud 
from app.crud.crud_bus import bus_crud
from app.crud.crud_conductor import conductor_crud
from app.crud.crud_sesion_conduccion import sesion_conduccion_crud

# Importar modelos para tipado
from app.models_db.cloud_database_models import Evento, Alerta, Bus, Conductor, SesionConduccion 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# --- Umbrales de Alerta (Ejemplo, AJUSTAR SEGÚN TUS NECESIDADES) ---
DISTRACTION_ALERT_THRESHOLD_SECONDS = 3  
FATIGUE_ALERT_THRESHOLD_SCORE = 0.8     
UNIDENTIFIED_DRIVER_ALERT_COOLDOWN_MINUTES = 5 

class EventProcessingService:
    """
    Capa de servicio para procesar eventos de monitoreo recibidos de las Jetsons.
    Maneja el almacenamiento de eventos, la evaluación de alertas y la vinculación de datos.
    """

    def process_events_batch(self, db: Session, events_data: List[Dict[str, Any]]) -> List[Evento]:
        """
        Procesa un lote de eventos de monitoreo recibidos de una Jetson Nano.
        Guarda los eventos y evalúa si se deben disparar alertas.

        Args:
            db (Session): La sesión de la base de datos.
            events_data (List[Dict[str, Any]]): Lista de diccionarios con datos de eventos.

        Returns:
            List[Evento]: Lista de objetos Evento guardados en la BD central.
        """
        logger.info(f"Procesando lote de {len(events_data)} eventos entrantes.")
        processed_events: List[Evento] = []

        for event_data_raw in events_data: # Renombramos para trabajar con una copia modificable
            event_data = event_data_raw.copy() # Aseguramos una copia para no modificar el original
            try:
                event_id_jetson = event_data.get('id') 
                if not event_id_jetson or not isinstance(event_id_jetson, str):
                    logger.warning(f"Evento sin ID válido. Saltando: {event_data.get('tipo_evento')}")
                    continue
                try:
                    event_data['id'] = uuid.UUID(event_id_jetson)
                except ValueError:
                    logger.warning(f"ID de evento '{event_id_jetson}' no es un UUID válido. Saltando.")
                    continue
                
                # Convertir timestamp_evento a datetime
                if 'timestamp_evento' in event_data and isinstance(event_data['timestamp_evento'], str):
                    try:
                        event_data['timestamp_evento'] = datetime.fromisoformat(event_data['timestamp_evento'])
                    except ValueError:
                        logger.warning(f"Formato de timestamp_evento inválido para evento {event_id_jetson}. Usando hora actual.")
                        event_data['timestamp_evento'] = datetime.utcnow() 

                # Asegurar que id_bus y id_conductor son UUIDs
                for field in ['id_bus', 'id_conductor']:
                    if field in event_data and isinstance(event_data[field], str) and event_data[field] != "00000000-0000-0000-0000-000000000000": 
                        try:
                            event_data[field] = uuid.UUID(event_data[field])
                        except ValueError:
                            logger.warning(f"ID inválido para {field} en evento {event_id_jetson}. Se establece a None.")
                            event_data[field] = None
                    elif event_data[field] == "00000000-0000-0000-0000-000000000000":
                        event_data[field] = None 

                # >>>>>>>>>>>>>>> CAMBIO AQUI: Renombrar id_sesion_conduccion_jetson a id_sesion_conduccion <<<<<<<<<<<<<
                id_sesion_conduccion_jetson_str = event_data.get('id_sesion_conduccion_jetson')
                event_data['id_sesion_conduccion'] = None # Inicializar con None
                if id_sesion_conduccion_jetson_str and isinstance(id_sesion_conduccion_jetson_str, str):
                    try:
                        id_sesion_conduccion_jetson_uuid = uuid.UUID(id_sesion_conduccion_jetson_str)
                        sesion_existente = sesion_conduccion_crud.get_by_jetson_session_id(db, id_sesion_conduccion_jetson_uuid)
                        if sesion_existente:
                            event_data['id_sesion_conduccion'] = id_sesion_conduccion_jetson_uuid # Usa el UUID real de la Jetson
                        else:
                            logger.warning(f"Sesión '{id_sesion_conduccion_jetson_str}' no encontrada en la nube para evento {event_id_jetson}. Evento no se vinculará a sesión.")
                    except ValueError:
                        logger.warning(f"ID de sesión '{id_sesion_conduccion_jetson_str}' no es un UUID válido. Evento no se vinculará a sesión.")
                
                # Quitar el campo original si existe en la data antes de pasar al modelo
                if 'id_sesion_conduccion_jetson' in event_data:
                    del event_data['id_sesion_conduccion_jetson']

                # Validar existencia de Bus y Conductor
                if event_data.get('id_bus') is None:
                    logger.warning(f"Evento {event_id_jetson} sin ID de bus válido. No se procesa.")
                    continue
                bus_existente = bus_crud.get(db, event_data['id_bus'])
                if not bus_existente:
                    logger.warning(f"Bus '{event_data['id_bus']}' no encontrado para evento {event_id_jetson}. No se procesa el evento.")
                    continue
                
                if event_data.get('id_conductor') is not None:
                    conductor_existente = conductor_crud.get(db, event_data['id_conductor'])
                    if not conductor_existente:
                        logger.warning(f"Conductor '{event_data['id_conductor']}' no encontrado para evento {event_id_jetson}. Se anula el vínculo.")
                        event_data['id_conductor'] = None 

                # Convertir floats de string si es necesario (ej. confidence_score_ia)
                if 'confidence_score_ia' in event_data and isinstance(event_data['confidence_score_ia'], str):
                    try:
                        event_data['confidence_score_ia'] = float(event_data['confidence_score_ia'])
                    except ValueError:
                        event_data['confidence_score_ia'] = None
                
                # Asegurar que los URLs de evidencia no son null si el campo es no-null en la DB
                if 'snapshot_url' not in event_data: event_data['snapshot_url'] = None
                if 'video_clip_url' not in event_data: event_data['video_clip_url'] = None

                # Crear el evento en la BD central
                new_db_event = evento_crud.create_or_update(db, event_data, unique_field='id')
                processed_events.append(new_db_event)
                logger.info(f"Evento ID {new_db_event.id} ({new_db_event.tipo_evento}) procesado y guardado.")

                # --- Evaluación de Alertas ---
                self._evaluate_for_alert(db, new_db_event)

            except Exception as e:
                logger.error(f"Error procesando evento: {event_data.get('id')} - {e}", exc_info=True)
        
        db.commit() # Un solo commit para todo el lote de eventos procesados
        return processed_events

    def _evaluate_for_alert(self, db: Session, event: Evento):
        """
        Evalúa un evento individual para determinar si debe disparar una alerta.
        """
        alert_triggered = False
        alert_type = None
        description = None
        severity = None

        if event.tipo_evento == 'Distraccion' and event.duracion_segundos is not None and event.duracion_segundos >= DISTRACTION_ALERT_THRESHOLD_SECONDS:
            alert_type = 'Distracción Prolongada'
            description = f"El conductor se distrajo por {event.duracion_segundos} segundos."
            severity = 'Crítica'
            alert_triggered = True
        elif event.tipo_evento == 'Fatiga' and event.confidence_score_ia is not None and event.confidence_score_ia >= FATIGUE_ALERT_THRESHOLD_SCORE:
            alert_type = 'Fatiga Severa'
            description = f"Alta probabilidad de fatiga (score: {event.confidence_score_ia})."
            severity = 'Crítica'
            alert_triggered = True
        elif event.tipo_evento == 'RegulacionConduccion' and event.subtipo_evento == 'Exceso Horas Conduccion':
            alert_type = 'Exceso Horas Conduccion'
            description = f"El conductor ha excedido el límite de horas de conducción."
            severity = 'Crítica'
            alert_triggered = True
        elif event.tipo_evento == 'Identificacion' and event.subtipo_evento == 'Conductor No Identificado':
            alert_type = 'Conductor No Identificado'
            description = f"Alerta: Conductor no identificado en el bus '{event.id_bus}'."
            severity = 'Alta'
            alert_triggered = True
            if self._is_on_cooldown(db, event.id_bus, 'Conductor No Identificado', UNIDENTIFIED_DRIVER_ALERT_COOLDOWN_MINUTES):
                logger.info(f"Alerta de 'Conductor No Identificado' para bus {event.id_bus} en periodo de enfriamiento. No se dispara.")
                alert_triggered = False


        if alert_triggered:
            try:
                alert_data = {
                    "id_evento": event.id,
                    "id_conductor": event.id_conductor if event.id_conductor else uuid.UUID('00000000-0000-0000-0000-000000000000'), 
                    "id_bus": event.id_bus,
                    "id_sesion_conduccion": event.id_sesion_conduccion,
                    "timestamp_alerta": event.timestamp_evento, 
                    "tipo_alerta": alert_type,
                    "descripcion": description,
                    "nivel_criticidad": severity,
                    "estado_alerta": "Activa" 
                }
                
                new_alert = alerta_crud.create(db, alert_data) 
                logger.info(f"ALERTA DISPARADA: {new_alert.tipo_alerta} para bus {new_alert.id_bus}, conductor {new_alert.id_conductor}. ID Alerta: {new_alert.id}")
                event.alerta_disparada = True 
                db.add(event) 
            except Exception as e:
                logger.error(f"Error al crear alerta para evento {event.id}: {e}", exc_info=True)


    def _is_on_cooldown(self, db: Session, bus_id: uuid.UUID, alert_type: str, cooldown_minutes: int) -> bool:
        """
        Verifica si una alerta de un tipo específico para un bus específico está en un período de enfriamiento.
        Esto previene el spam de alertas por la misma condición.
        """
        cooldown_threshold = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
        last_alert: Optional[Alerta] = db.query(Alerta).filter(
            Alerta.id_bus == bus_id,
            Alerta.tipo_alerta == alert_type
        ).order_by(Alerta.timestamp_alerta.desc()).first()

        if last_alert and last_alert.timestamp_alerta >= cooldown_threshold:
            return True 
        return False


# Crea una instancia de EventProcessingService para ser utilizada por los endpoints API.
event_processing_service = EventProcessingService()