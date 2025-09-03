# app.py
from flask_cors import CORS
from flask import Flask, jsonify, request, send_from_directory
import logging
from datetime import datetime
import os


# Importaciones de configuración
from app.config.settings import settings
from app.config.database import db, init_db_with_app, create_db_and_tables # Importamos la instancia de db y funciones
from app.models_db.cloud_database_models import Base # Asegúrate de que esta importación sea correcta

# Configuración del logger principal de la aplicación
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """
    Función principal para crear y configurar la aplicación Flask.
    """
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins=["http://localhost:3000", "https://movai-production-bd1b.up.railway.app"])
    # --- Configuración de la aplicación ---
    # Carga las configuraciones desde el objeto settings
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Recomendado para rendimiento
    app.config["SECRET_KEY"] = settings.SECRET_KEY # Para sesiones, JWT, etc.
    app.config["DEBUG"] = settings.DEBUG_MODE # Activa/desactiva el modo depuración

    # --- Inicializar extensiones ---
    init_db_with_app(app) # Inicializa Flask-SQLAlchemy con la aplicación

    # --- Registrar Blueprints de la API ---
    # Un blueprint ayuda a organizar grupos de rutas y otros códigos.
    # Crearemos un blueprint principal para la API y luego versiones.
    from app.api import create_api_blueprint
    api_blueprint = create_api_blueprint()
    app.register_blueprint(api_blueprint, url_prefix='/api') # Todas las rutas de API bajo /api

    # --- Manejo de errores globales (Opcional, Flask ya tiene uno básico) ---
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 Not Found: {request.url}")
        return jsonify({"message": "Recurso no encontrado", "code": 404}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.exception(f"500 Internal Server Error: {error}")
        return jsonify({"message": "Error interno del servidor", "code": 500}), 500
    
    @app.route('/static/uploads/<path:filename>')
    def uploaded_file(filename):
        # El 'filename' aquí contendrá la ruta relativa desde 'uploads/'
        # Ej. 'cedula_conductor/video/training_video_xyz.mp4'
        # Necesitamos extraer la parte inicial de la cédula para buscar el directorio base
        parts = filename.split(os.sep)
        if len(parts) >= 2: # Esperamos algo como 'cedula/tipo_media/nombre_archivo.ext'
            conductor_cedula = parts[0]
            # Construye la ruta real en el disco
            # Asegúrate de que esta ruta coincida con cómo guardas los archivos en training_data_service.py
            actual_file_path = os.path.join(settings.STORAGE_PATH, conductor_cedula, *parts[1:])

            if os.path.exists(actual_file_path):
                # Extrae el directorio base y el nombre del archivo para send_from_directory
                directory = os.path.dirname(actual_file_path)
                file_name = os.path.basename(actual_file_path)
                return send_from_directory(directory, file_name)

        return jsonify({"message": "Archivo no encontrado."}), 404

    # --- Ruta de prueba simple ---
    @app.route('/')
    def index():
        return jsonify({"message": "Bienvenido al sistema de monitoreo de conductores (Backend en la Nube)"})

    # --- Creación de tablas de la base de datos (para desarrollo) ---
    # Esto se puede ejecutar manualmente o al inicio de la app en modo dev.
    # Para producción, se usarán migraciones (Alembic).
    with app.app_context(): # Es necesario un contexto de aplicación para interactuar con la BD
        create_db_and_tables() # Llama a la función para crear tablas

    logger.info("Aplicación Flask creada y configurada.")
    return app
    

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == '__main__':
    app = create_app()

    logger.info(f"Aplicación Flask iniciada en modo DEBUG: {app.config['DEBUG']}")
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])