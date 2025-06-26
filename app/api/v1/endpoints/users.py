# app/api/v1/endpoints/users.py
from flask import Blueprint, request, jsonify
from typing import Optional, List
import uuid
import logging

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para Usuarios
from app.services.user_service import user_service
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import Usuario 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Usuarios
users_bp = Blueprint('users_api', __name__)

@users_bp.route('/', methods=['POST'])
def create_user():
    """
    Endpoint API para registrar un nuevo usuario.
    Requiere: Cuerpo JSON con 'username' (str), 'password' (str), 'email' (str), 'rol' (str).
              'id_empresa' (UUID str, opcional).
    """
    logger.info("Solicitud recibida para crear un nuevo usuario.")
    user_data = request.get_json()

    if not user_data:
        logger.warning("No se proporcionó cuerpo JSON para el registro del usuario.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los datos del usuario."}), 400
    
    # Validación básica de campos requeridos
    required_fields = ['username', 'password', 'email', 'rol']
    if not all(field in user_data for field in required_fields):
        logger.warning(f"Faltan campos requeridos para el registro del usuario: {required_fields}.")
        return jsonify({"message": f"Los campos {required_fields} son requeridos."}), 400

    try:
        # La contraseña se hashea dentro del user_service.create_new_user
        new_user = user_service.create_new_user(db.session, user_data)

        if new_user:
            response_data = {
                "id": str(new_user.id),
                "username": new_user.username,
                "email": new_user.email,
                "rol": new_user.rol,
                "activo": new_user.activo,
                "id_empresa": str(new_user.id_empresa) if new_user.id_empresa else None
            }
            logger.info(f"Usuario '{new_user.username}' registrado exitosamente.")
            return jsonify(response_data), 201 # 201 Created
        else:
            # El servicio ya maneja mensajes de error específicos (ej. username/email duplicado, empresa no encontrada)
            return jsonify({"message": "Fallo al registrar el usuario. Verifique los datos."}), 400
    except Exception as e:
        logger.exception(f"Error registrando usuario: {e}")
        return jsonify({"message": "Error interno del servidor al registrar el usuario."}), 500

@users_bp.route('/<uuid:user_id>', methods=['GET'])
def get_user_details(user_id: uuid.UUID):
    """
    Endpoint API para obtener los detalles de un usuario específico por su ID.
    """
    logger.info(f"Solicitud recibida para detalles del usuario ID: {user_id}")
    try:
        user = user_service.get_user_details(db.session, user_id)
        if user:
            response_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "id_empresa": str(user.id_empresa) if user.id_empresa else None,
                "rol": user.rol,
                "activo": user.activo,
                "fecha_creacion": user.fecha_creacion.isoformat(),
                "ultimo_login_at": user.ultimo_login_at.isoformat() if user.ultimo_login_at else None,
                "last_updated_at": user.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            logger.warning(f"Usuario ID {user_id} no encontrado.")
            return jsonify({"message": "Usuario no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener detalles del usuario ID {user_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener el usuario."}), 500

@users_bp.route('/by_username', methods=['GET'])
def get_user_by_username():
    """
    Endpoint API para obtener los detalles de un usuario por su nombre de usuario.
    Query parameter: username (str).
    """
    username = request.args.get('username')
    if not username:
        logger.warning("No se proporcionó el username para buscar el usuario.")
        return jsonify({"message": "El parámetro 'username' es requerido."}), 400
    
    logger.info(f"Solicitud recibida para el usuario con username: {username}")
    try:
        user = user_service.get_user_by_username(db.session, username)
        if user:
            response_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "rol": user.rol,
                "activo": user.activo,
                "id_empresa": str(user.id_empresa) if user.id_empresa else None
            }
            logger.info(f"Usuario con username '{username}' encontrado y detalles enviados.")
            return jsonify(response_data), 200
        else:
            logger.warning(f"Usuario con username '{username}' no encontrado.")
            return jsonify({"message": "Usuario no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener usuario por username {username}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener el usuario por username."}), 500

@users_bp.route('/', methods=['GET'])
def get_all_users():
    """
    Endpoint API para obtener una lista de todos los usuarios con paginación.
    Query parameters: skip (int, default 0), limit (int, default 100), id_empresa (UUID str, opcional).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    empresa_id_str = request.args.get('id_empresa')
    empresa_id: Optional[uuid.UUID] = None

    if empresa_id_str:
        try:
            empresa_id = uuid.UUID(empresa_id_str)
        except ValueError:
            return jsonify({"message": "El 'id_empresa' proporcionado no es un UUID válido."}), 400

    logger.info(f"Solicitud recibida para todos los usuarios (skip={skip}, limit={limit}, id_empresa={empresa_id}).")
    
    try:
        if empresa_id:
            users = user_service.get_users_by_empresa(db.session, empresa_id, skip=skip, limit=limit)
        else:
            users = user_service.get_all_users(db.session, skip=skip, limit=limit)
        
        response_data = []
        for user in users:
            response_data.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "rol": user.rol,
                "activo": user.activo,
                "id_empresa": str(user.id_empresa) if user.id_empresa else None
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener todos los usuarios: {e}")
        return jsonify({"message": "Error interno del servidor al obtener los usuarios."}), 500

@users_bp.route('/<uuid:user_id>', methods=['PUT'])
def update_user_details(user_id: uuid.UUID):
    """
    Endpoint API para actualizar los detalles de un usuario existente.
    Requiere: Cuerpo JSON con los campos a actualizar (ej. 'email', 'rol', 'activo', 'password').
    """
    logger.info(f"Solicitud recibida para actualizar usuario ID: {user_id}")
    updates = request.get_json()

    if not updates:
        logger.warning(f"No se proporcionó cuerpo JSON para actualizar el usuario ID {user_id}.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los campos a actualizar."}), 400

    try:
        # La contraseña se hashea dentro del user_service.update_user_details
        updated_user = user_service.update_user_details(db.session, user_id, updates)
        if updated_user:
            response_data = {
                "id": str(updated_user.id),
                "username": updated_user.username,
                "email": updated_user.email,
                "rol": updated_user.rol,
                "activo": updated_user.activo,
                "last_updated_at": updated_user.last_updated_at.isoformat(),
                "id_empresa": str(updated_user.id_empresa) if updated_user.id_empresa else None
            }
            logger.info(f"Usuario ID {user_id} actualizado exitosamente.")
            return jsonify(response_data), 200
        else:
            return jsonify({"message": "Usuario no encontrado o no se pudo actualizar. Verifique los datos o ID."}), 404
    except Exception as e:
        logger.exception(f"Error al actualizar usuario ID {user_id}: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar el usuario."}), 500

@users_bp.route('/<uuid:user_id>', methods=['DELETE'])
def delete_user(user_id: uuid.UUID):
    """
    Endpoint API para eliminar un usuario del sistema.
    """
    logger.info(f"Solicitud recibida para eliminar usuario ID: {user_id}")
    try:
        deleted = user_service.delete_user(db.session, user_id)
        if deleted:
            logger.info(f"Usuario ID {user_id} eliminado exitosamente.")
            return jsonify({"message": "Usuario eliminado correctamente."}), 204 # 204 No Content
        else:
            return jsonify({"message": "Usuario no encontrado o no se pudo eliminar (puede tener registros asociados)."}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar usuario ID {user_id}: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar el usuario."}), 500

# Considerar un endpoint para obtener el usuario autenticado (requerirá autenticación JWT)
# @users_bp.route('/me', methods=['GET'])
# def get_me():
#     """
#     Endpoint API para obtener el perfil del usuario actualmente autenticado.
#     """
#     # Requiere un decorador de autenticación JWT
#     # current_user_id = get_current_user_id_from_token() # Función que obtendrá el ID del token
#     # user = user_service.get_user_details(db.session, current_user_id)
#     # if user: ... else: ...
#     pass