# app/models_db/cloud_database_models.py
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, DateTime, Date, Boolean, Numeric, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID 
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Base declarativa para los modelos ORM de la Nube
Base = declarative_base()

# --- Tablas de Información Maestra (Cloud) ---

class Empresa(Base): 
    __tablename__ = 'empresas' 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    nombre_empresa = Column(String, nullable=False)
    nit = Column(String, unique=True, nullable=False)
    direccion = Column(String)
    telefono_contacto = Column(String)
    email_contacto = Column(String)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    buses = relationship("Bus", back_populates="empresa") 
    conductores = relationship("Conductor", back_populates="empresa") 
    usuarios = relationship("Usuario", back_populates="empresa") 

    def __repr__(self):
        return f"<Empresa(id='{self.id}', nombre_empresa='{self.nombre_empresa}')>"

class Bus(Base):
    __tablename__ = 'buses'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_empresa = Column(UUID(as_uuid=True), ForeignKey('empresas.id'), nullable=False) 
    placa = Column(String, nullable=False)
    numero_interno = Column(String, nullable=False) 
    marca = Column(String)
    modelo = Column(String)
    anio_fabricacion = Column(Integer)
    capacidad_pasajeros = Column(Integer)
    estado_operativo = Column(String, default='Activo', nullable=False) 
    ultima_conexion_at = Column(DateTime) 
    ubicacion_actual_gps = Column(String) 
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    jetson_nano_device = relationship("JetsonNano", back_populates="bus", uselist=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="buses") 
    eventos = relationship("Evento", back_populates="bus")
    alertas = relationship("Alerta", back_populates="bus")
    sesiones_conduccion = relationship("SesionConduccion", back_populates="bus")
    asignaciones_programadas = relationship("AsignacionProgramada", back_populates="bus")

    def __repr__(self):
        return f"<Bus(id='{self.id}', placa='{self.placa}', numero_interno='{self.numero_interno}')>"

class Conductor(Base):
    __tablename__ = 'conductores'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_empresa = Column(UUID(as_uuid=True), ForeignKey('empresas.id'), nullable=False) 
    cedula = Column(String, unique=True, nullable=False)
    nombre_completo = Column(String, nullable=False)
    fecha_nacimiento = Column(Date)
    telefono_contacto = Column(String)
    email = Column(String)
    licencia_conduccion = Column(String)
    tipo_licencia = Column(String) 
    fecha_expiracion_licencia = Column(Date)
    activo = Column(Boolean, default=True, nullable=False)
    codigo_qr_hash = Column(String, unique=True) 
    foto_perfil_url = Column(String) 
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Campos específicos para Reconocimiento Facial y Entrenamiento
    id_video_entrenamiento_principal = Column(UUID(as_uuid=True), ForeignKey('videos_entrenamiento.id'), nullable=True)
    caracteristicas_faciales_embedding = Column(JSON) 

    # Relaciones
    empresa = relationship("Empresa", back_populates="conductores") 
    eventos = relationship("Evento", back_populates="conductor")
    calificaciones = relationship("CalificacionConductor", back_populates="conductor")
    alertas = relationship("Alerta", back_populates="conductor")
    sesiones_conduccion = relationship("SesionConduccion", back_populates="conductor")
    asignaciones_programadas = relationship("AsignacionProgramada", back_populates="conductor")
    
    videos_entrenamiento = relationship("VideoEntrenamiento", 
                                        back_populates="conductor",
                                        foreign_keys="[VideoEntrenamiento.id_conductor]") 
    
    def __repr__(self):
        return f"<Conductor(id='{self.id}', cedula='{self.cedula}', nombre_completo='{self.nombre_completo}')>"

class AsignacionProgramada(Base):
    __tablename__ = 'asignaciones_programadas' 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_conductor = Column(UUID(as_uuid=True), ForeignKey('conductores.id'), nullable=False)
    id_bus = Column(UUID(as_uuid=True), ForeignKey('buses.id'), nullable=False)
    
    fecha_inicio_programada = Column(DateTime, nullable=False)
    fecha_fin_programada = Column(DateTime, nullable=True) 
    tipo_programacion = Column(String, nullable=False) 
    turno_especifico = Column(String, nullable=True) 
    
    activo = Column(Boolean, default=True, nullable=False) 
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    conductor = relationship("Conductor", back_populates="asignaciones_programadas")
    bus = relationship("Bus", back_populates="asignaciones_programadas")

    def __repr__(self):
        return (f"<AsignacionProgramada(id='{self.id}', conductor='{self.id_conductor}', "
                f"bus='{self.id_bus}', inicio_prog='{self.fecha_inicio_programada}', tipo='{self.tipo_programacion}')>")

class SesionConduccion(Base):
    __tablename__ = 'sesiones_conduccion' 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_sesion_conduccion_jetson = Column(UUID(as_uuid=True), unique=True, nullable=False) 
    
    id_conductor = Column(UUID(as_uuid=True), ForeignKey('conductores.id'), nullable=False)
    id_bus = Column(UUID(as_uuid=True), ForeignKey('buses.id'), nullable=False)

    fecha_inicio_real = Column(DateTime, nullable=False) 
    fecha_fin_real = Column(DateTime, nullable=True) 
    
    estado_sesion = Column(String, default='Activa', nullable=False) 
    duracion_total_seg = Column(Numeric, nullable=True) 
    
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    conductor = relationship("Conductor", back_populates="sesiones_conduccion")
    bus = relationship("Bus", back_populates="sesiones_conduccion")
    eventos = relationship("Evento", back_populates="sesion_conduccion")
    alertas = relationship("Alerta", back_populates="sesion_conduccion")

    def __repr__(self):
        return (f"<SesionConduccion(id='{self.id}', sesion_jetson_id='{self.id_sesion_conduccion_jetson}', "
                f"conductor='{self.id_conductor}', bus='{self.id_bus}', estado='{self.estado_sesion}')>")


class JetsonNano(Base):
    __tablename__ = 'jetson_nanos'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_hardware_jetson = Column(String, unique=True, nullable=False) 
    id_bus = Column(UUID(as_uuid=True), ForeignKey('buses.id'), nullable=True) 
    version_firmware = Column(String) 
    estado_salud = Column(String, default='Desconocido', nullable=False) 
    ultima_actualizacion_firmware_at = Column(DateTime)
    ultima_conexion_cloud_at = Column(DateTime) 
    last_telemetry_at = Column(DateTime) # Keep this to track last telemetry arrival
    fecha_instalacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    observaciones = Column(Text)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    bus = relationship("Bus", back_populates="jetson_nano_device") 
    telemetry_data = relationship("JetsonTelemetry", back_populates="jetson_device") # New relationship

    def __repr__(self):
        return (f"<JetsonNano(id='{self.id}', hardware_id='{self.id_hardware_jetson}', "
                f"estado='{self.estado_salud}', bus_id='{self.id_bus}')>")

class JetsonTelemetry(Base): # NEW TABLE
    __tablename__ = 'jetson_telemetry'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_hardware_jetson = Column(String, ForeignKey('jetson_nanos.id_hardware_jetson'), nullable=False) # Link to JetsonNano by its hardware ID
    timestamp_telemetry = Column(DateTime, default=datetime.utcnow, nullable=False)
    ram_usage_gb = Column(Numeric)
    cpu_usage_percent = Column(Numeric)
    disk_usage_gb = Column(Numeric)
    disk_usage_percent = Column(Numeric)
    temperatura_celsius = Column(Numeric)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to JetsonNano (one-to-many, a JetsonNano can have many telemetry records)
    jetson_device = relationship("JetsonNano", back_populates="telemetry_data")

    def __repr__(self):
        return (f"<JetsonTelemetry(id='{self.id}', hardware_id='{self.id_hardware_jetson}', "
                f"timestamp='{self.timestamp_telemetry}', cpu='{self.cpu_usage_percent}')>")

# --- Datos Transaccionales (Cloud) ---

class Evento(Base):
    __tablename__ = 'eventos'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_local_jetson = Column(Integer, nullable=True) 
    id_bus = Column(UUID(as_uuid=True), ForeignKey('buses.id'), nullable=False)
    id_conductor = Column(UUID(as_uuid=True), ForeignKey('conductores.id'), nullable=False)
    id_sesion_conduccion = Column(UUID(as_uuid=True), ForeignKey('sesiones_conduccion.id_sesion_conduccion_jetson'), nullable=True) 
    timestamp_evento = Column(DateTime, nullable=False)
    tipo_evento = Column(String, nullable=False) 
    subtipo_evento = Column(String) 
    duracion_segundos = Column(Numeric) 
    severidad = Column(String) 
    confidence_score_ia = Column(Numeric) 
    alerta_disparada = Column(Boolean, default=False, nullable=False)
    ubicacion_gps_evento = Column(String)
    snapshot_url = Column(String) 
    video_clip_url = Column(String) 
    metadatos_ia_json = Column(JSON) 
    sent_to_cloud_at = Column(DateTime) 
    processed_in_cloud_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 

    # Relaciones
    bus = relationship("Bus", back_populates="eventos")
    conductor = relationship("Conductor", back_populates="eventos")
    sesion_conduccion = relationship("SesionConduccion", back_populates="eventos")
    alerta = relationship("Alerta", uselist=False, back_populates="evento") 

    def __repr__(self):
        return (f"<Evento(id='{self.id}', bus='{self.id_bus}', conductor='{self.id_conductor}', "
                f"tipo='{self.tipo_evento}', subtipo='{self.subtipo_evento}', time='{self.timestamp_evento}')>")

class CalificacionConductor(Base):
    __tablename__ = 'calificaciones_conductores'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_conductor = Column(UUID(as_uuid=True), ForeignKey('conductores.id'), nullable=False)
    fecha_calificacion = Column(Date, nullable=False) 
    periodo_calificacion = Column(String, default='Diario', nullable=False) 
    puntaje_total = Column(Numeric, nullable=False) 
    puntaje_distraccion = Column(Numeric)
    puntaje_fatiga = Column(Numeric)
    puntaje_exceso_tiempo_conduccion = Column(Numeric) 
    num_eventos_distraccion = Column(Integer, default=0)
    num_eventos_fatiga = Column(Integer, default=0)
    num_eventos_exceso_tiempo_conduccion = Column(Integer, default=0) 
    duracion_total_distraccion_seg = Column(Numeric, default=0)
    duracion_total_fatiga_seg = Column(Numeric, default=0)
    km_recorridos_periodo = Column(Numeric) 
    observaciones = Column(Text)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    conductor = relationship("Conductor", back_populates="calificaciones")

    def __repr__(self):
        return (f"<CalificacionConductor(id='{self.id}', conductor='{self.id_conductor}', "
                f"fecha='{self.fecha_calificacion}', puntaje='{self.puntaje_total}')>")

class Alerta(Base):
    __tablename__ = 'alertas'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_evento = Column(UUID(as_uuid=True), ForeignKey('eventos.id'), nullable=True) 
    id_conductor = Column(UUID(as_uuid=True), ForeignKey('conductores.id'), nullable=False)
    id_bus = Column(UUID(as_uuid=True), ForeignKey('buses.id'), nullable=False)
    id_sesion_conduccion = Column(UUID(as_uuid=True), ForeignKey('sesiones_conduccion.id_sesion_conduccion_jetson'), nullable=True)
    timestamp_alerta = Column(DateTime, default=datetime.utcnow, nullable=False)
    tipo_alerta = Column(String, nullable=False) 
    descripcion = Column(Text, nullable=False)
    nivel_criticidad = Column(String, nullable=False) 
    estado_alerta = Column(String, default='Activa', nullable=False) 
    
    gestionada_por_id_usuario = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    fecha_gestion = Column(DateTime, nullable=True) 
    tipo_gestion = Column(String, nullable=True) 
    comentarios_gestion = Column(Text) 
    
    notificado_canales = Column(JSON) 

    # Relaciones
    conductor = relationship("Conductor", back_populates="alertas")
    bus = relationship("Bus", back_populates="alertas")
    evento = relationship("Evento", back_populates="alerta")
    sesion_conduccion = relationship("SesionConduccion", back_populates="alertas")

    gestionada_por_usuario = relationship("Usuario", back_populates="alertas_gestionadas")

    def __repr__(self):
        return (f"<Alerta(id='{self.id}', tipo='{self.tipo_alerta}', criticidad='{self.nivel_criticidad}', "
                f"estado='{self.estado_alerta}', time='{self.timestamp_alerta}')>")

# --- Datos de Entrenamiento (Cloud) ---

class VideoEntrenamiento(Base):
    __tablename__ = 'videos_entrenamiento'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_conductor = Column(UUID(as_uuid=True), ForeignKey('conductores.id'), nullable=False)
    url_video_original = Column(String, nullable=False) 
    fecha_captura = Column(Date)
    duracion_segundos = Column(Numeric)
    estado_procesamiento = Column(String, default='Pendiente', nullable=False)
    metadata_ia_video = Column(JSON) 
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    conductor = relationship("Conductor", back_populates="videos_entrenamiento", foreign_keys="[VideoEntrenamiento.id_conductor]")
    imagenes = relationship("ImagenEntrenamiento", back_populates="video_entrenamiento")

    def __repr__(self):
        return f"<VideoEntrenamiento(id='{self.id}', conductor='{self.id_conductor}', url='{self.url_video_original}')>"

class ImagenEntrenamiento(Base):
    __tablename__ = 'imagenes_entrenamiento'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    id_video_entrenamiento = Column(UUID(as_uuid=True), ForeignKey('videos_entrenamiento.id'), nullable=False) # <<<<< CORREGIDO DE as_ass_uuid a as_uuid
    url_imagen = Column(String, nullable=False) 
    timestamp_en_video_seg = Column(Numeric) 
    es_principal = Column(Boolean, default=False, nullable=False) 
    bounding_box_json = Column(JSON) 
    caracteristicas_faciales_embedding = Column(JSON) 

    # Relaciones
    video_entrenamiento = relationship("VideoEntrenamiento", back_populates="imagenes")

    def __repr__(self):
        return f"<ImagenEntrenamiento(id='{self.id}', video_id='{self.id_video_entrenamiento}', url='{self.url_imagen}')>"

# --- Tablas de Usuario (Cloud) ---

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) 
    email = Column(String, unique=True, nullable=False)
    id_empresa = Column(UUID(as_uuid=True), ForeignKey('empresas.id'), nullable=True) 
    rol = Column(String, nullable=False) 
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    ultimo_login_at = Column(DateTime)

    # Relaciones
    empresa = relationship("Empresa", back_populates="usuarios") 
    alertas_gestionadas = relationship("Alerta", back_populates="alertas_gestionadas") 

    def __repr__(self):
        return f"<Usuario(id='{self.id}', username='{self.username}', rol='{self.rol}')>"

# Para la relación de Alerta con Usuario (gestión)
Alerta.gestionada_por_usuario = relationship("Usuario", back_populates="alertas_gestionadas")