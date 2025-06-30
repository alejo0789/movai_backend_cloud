# app/api/v1/__init__.py
from flask import Blueprint

def create_v1_blueprint() -> Blueprint:
    """
    Crea y configura el Blueprint para la versión 1 de la API.
    Aquí se registrarán todos los endpoints específicos de la v1.
    """
    v1_bp = Blueprint('v1_api', __name__)

    # --- Registrar Endpoints (Rutas) de la API v1 ---
    # Importa y registra cada módulo de endpoints aquí.
    
    # Endpoints para la gestión de Empresas
    from app.api.v1.endpoints import empresas
    v1_bp.register_blueprint(empresas.empresas_bp, url_prefix='/empresas') # <<<<<<<<<<<<<<<< REGISTRADO

    # Otros endpoints (comentados por ahora, se añadirán a medida que los crees)
    # from app.api.v1.endpoints import auth
    # v1_bp.register_blueprint(auth.auth_bp, url_prefix='/auth') 
    from app.api.v1.endpoints import users
    v1_bp.register_blueprint(users.users_bp, url_prefix='/users') 
    from app.api.v1.endpoints import buses
    v1_bp.register_blueprint(buses.buses_bp, url_prefix='/buses')
    from app.api.v1.endpoints import conductores
    v1_bp.register_blueprint(conductores.conductores_bp, url_prefix='/conductores')
    from app.api.v1.endpoints import asignaciones_programadas
    v1_bp.register_blueprint(asignaciones_programadas.asignaciones_programadas_bp, url_prefix='/asignaciones-programadas')
    from app.api.v1.endpoints import sesiones_conduccion
    v1_bp.register_blueprint(sesiones_conduccion.sesiones_conduccion_bp, url_prefix='/sesiones-conduccion')
    from app.api.v1.endpoints import eventos
    v1_bp.register_blueprint(eventos.eventos_bp, url_prefix='/eventos')
    from app.api.v1.endpoints import alertas
    v1_bp.register_blueprint(alertas.alertas_bp, url_prefix='/alertas')
    # Endpoints para la gestión de Datos de Entrenamiento (Videos/Imágenes)
    from app.api.v1.endpoints import videos_images 
    v1_bp.register_blueprint(videos_images.training_data_bp, url_prefix='/training-data') 
    from app.api.v1.endpoints import jetson_nanos
    v1_bp.register_blueprint(jetson_nanos.jetson_nanos_bp, url_prefix='/jetson-nanos')
    # from app.api.v1.endpoints import reports
    # v1_bp.register_blueprint(reports.reports_bp, url_prefix='/reports')

    return v1_bp