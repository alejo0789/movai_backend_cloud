# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_sqlalchemy import SQLAlchemy # Si usas Flask-SQLAlchemy

# Importamos la instancia de la configuración de la aplicación
from app.config.settings import settings
# Importamos la base declarativa de tus modelos (Cloud)
from app.models_db.cloud_database_models import Base # Asegúrate de que esta importación sea correcta

# --- Configuración del Motor de la Base de Datos ---
# Usamos la URL de la base de datos cargada desde las configuraciones
engine = create_engine(settings.DATABASE_URL)

# --- Configuración de la Sesión de la Base de Datos ---
# Para Flask, a menudo se usa Flask-SQLAlchemy, que gestiona las sesiones.
# Si no usas Flask-SQLAlchemy, puedes usar sessionmaker directamente.

# Opción 1: Si usas Flask-SQLAlchemy (Más recomendado con Flask)
db = SQLAlchemy()

def init_db_with_app(app):
    """Inicializa la extensión Flask-SQLAlchemy con la aplicación Flask."""
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Deshabilita seguimiento de modificaciones para mejor rendimiento
    db.init_app(app)

    # Si quieres usar un pool de conexiones gestionado por SQLAlchemy directamente
    # app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    #     'pool_size': 10,
    #     'max_overflow': 20,
    #     'pool_recycle': 3600
    # }

# Opción 2: Si usas solo SQLAlchemy (sin Flask-SQLAlchemy)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Si necesitas una sesión por request en Flask sin Flask-SQLAlchemy,
# usaría un patrón como un decorador de request o un app context.
# Para este proyecto, con Flask, recomiendo la Opción 1.

def create_db_and_tables():
    """
    Crea todas las tablas definidas en 'cloud_database_models.py' en la base de datos.
    Útil para el desarrollo inicial. En producción, se usarán migraciones (Alembic).
    """
    Base.metadata.create_all(bind=engine)
    print("Tablas de la base de datos central creadas/verificadas.")