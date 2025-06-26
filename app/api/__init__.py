# app/api/__init__.py
from flask import Blueprint

def create_api_blueprint() -> Blueprint:
    """
    Crea y configura el Blueprint principal para la API.
    Aquí se registrarán las diferentes versiones de la API (ej. v1, v2).
    """
    api_bp = Blueprint('api', __name__)

    # --- Registrar Blueprints de versiones de la API ---
    # Importa y registra el Blueprint de la versión v1
    from app.api.v1 import create_v1_blueprint
    v1_bp = create_v1_blueprint()
    api_bp.register_blueprint(v1_bp, url_prefix='/v1') # Rutas de v1 bajo /api/v1

    # Puedes añadir más versiones aquí si el proyecto escala (ej. /v2)
    # from app.api.v2 import create_v2_blueprint
    # v2_bp = create_v2_blueprint()
    # api_bp.register_blueprint(v2_bp, url_prefix='/v2')

    return api_bp