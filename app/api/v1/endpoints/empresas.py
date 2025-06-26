# app/api/v1/endpoints/empresas.py
from flask import Blueprint, request, jsonify
from typing import Optional, List
import uuid
import logging

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db # <<<<<<<<<<<<<<<< CAMBIO AQUI: Importar 'db' directamente
# Import the service layer for Empresas
from app.services.empresa_service import empresa_service
# Import the schemas for validation (conceptual, as we haven't defined them yet)
# from app.api.v1.schemas.empresa_schema import EmpresaCreate, EmpresaUpdate, EmpresaResponse

# Setup logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Create a Blueprint for Empresas endpoints
empresas_bp = Blueprint('empresas_api', __name__)

@empresas_bp.route('/', methods=['POST'])
def create_empresa():
    """
    API endpoint to register a new company.
    Requires: JSON body with 'nombre_empresa' (str), 'nit' (str).
    """
    logger.info("Received request to create a new company.")
    empresa_data = request.get_json()

    if not empresa_data:
        logger.warning("No JSON body provided for company creation.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los datos de la empresa."}), 400
    
    if 'nombre_empresa' not in empresa_data or 'nit' not in empresa_data:
        logger.warning("Missing required fields for company creation.")
        return jsonify({"message": "Los campos 'nombre_empresa' y 'nit' son requeridos."}), 400

    # Get the database session from Flask-SQLAlchemy
    # db_session = db.session # <<<<<<<<<<<<<<<< CAMBIO AQUI: Acceder a la sesión
    # No necesitamos un try/finally con db_session.close() porque Flask-SQLAlchemy lo gestiona
    
    try:
        # Pasa la sesión gestionada por Flask-SQLAlchemy al servicio
        new_empresa = empresa_service.register_new_empresa(db.session, empresa_data) # <<<<<<<<<<<< PASAR db.session

        if new_empresa:
            response_data = {
                "id": str(new_empresa.id),
                "nombre_empresa": new_empresa.nombre_empresa,
                "nit": new_empresa.nit,
                "activo": new_empresa.activo,
                "fecha_registro": new_empresa.fecha_registro.isoformat() 
            }
            logger.info(f"Company '{new_empresa.nombre_empresa}' created successfully.")
            return jsonify(response_data), 201 
        else:
            return jsonify({"message": f"Fallo al registrar la empresa. El NIT '{empresa_data.get('nit')}' ya puede existir."}), 409 
    except Exception as e:
        logger.exception(f"Error creating company: {e}")
        return jsonify({"message": "Error interno del servidor al crear la empresa."}), 500
    # No hay db.close() aquí, Flask-SQLAlchemy lo hace automáticamente.


@empresas_bp.route('/<uuid:empresa_id>', methods=['GET'])
def get_empresa_details(empresa_id: uuid.UUID):
    """
    API endpoint to retrieve details of a specific company by its ID.
    """
    logger.info(f"Received request for company details ID: {empresa_id}")
    # db_session = db.session # Acceder a la sesión
    try:
        empresa = empresa_service.get_empresa_details(db.session, empresa_id) # <<<<<<<<<<<< PASAR db.session
        if empresa:
            response_data = {
                "id": str(empresa.id),
                "nombre_empresa": empresa.nombre_empresa,
                "nit": empresa.nit,
                "direccion": empresa.direccion,
                "telefono_contacto": empresa.telefono_contacto,
                "email_contacto": empresa.email_contacto,
                "activo": empresa.activo,
                "fecha_registro": empresa.fecha_registro.isoformat(),
                "last_updated_at": empresa.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            logger.warning(f"Company ID {empresa_id} not found.")
            return jsonify({"message": "Empresa no encontrada."}), 404
    except Exception as e:
        logger.exception(f"Error retrieving company ID {empresa_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener la empresa."}), 500
    # No hay db.close() aquí.

@empresas_bp.route('/', methods=['GET'])
def get_all_empresas():
    """
    API endpoint to retrieve a list of all companies with pagination.
    Query parameters: skip (int, default 0), limit (int, default 100).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    logger.info(f"Received request for all companies (skip={skip}, limit={limit}).")
    
    # db_session = db.session # Acceder a la sesión
    try:
        empresas = empresa_service.get_all_empresas(db.session, skip=skip, limit=limit) # <<<<<<<<<<<< PASAR db.session
        response_data = []
        for empresa in empresas:
            response_data.append({
                "id": str(empresa.id),
                "nombre_empresa": empresa.nombre_empresa,
                "nit": empresa.nit,
                "activo": empresa.activo
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error retrieving all companies: {e}")
        return jsonify({"message": "Error interno del servidor al obtener las empresas."}), 500
    # No hay db.close() aquí.

@empresas_bp.route('/<uuid:empresa_id>', methods=['PUT'])
def update_empresa_details(empresa_id: uuid.UUID):
    """
    API endpoint to update details for an existing company.
    Requires: JSON body with fields to update.
    """
    logger.info(f"Received request to update company ID: {empresa_id}")
    updates = request.get_json()

    if not updates:
        logger.warning(f"No JSON body provided for updating company ID {empresa_id}.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los campos a actualizar."}), 400

    # db_session = db.session # Acceder a la sesión
    try:
        updated_empresa = empresa_service.update_empresa_details(db.session, empresa_id, updates) # <<<<<<<<<<<< PASAR db.session
        if updated_empresa:
            response_data = {
                "id": str(updated_empresa.id),
                "nombre_empresa": updated_empresa.nombre_empresa,
                "nit": updated_empresa.nit,
                "activo": updated_empresa.activo,
                "last_updated_at": updated_empresa.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            return jsonify({"message": "Empresa no encontrada o no se pudo actualizar."}), 404
    except Exception as e:
        logger.exception(f"Error updating company ID {empresa_id}: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar la empresa."}), 500
    # No hay db.close() aquí.

@empresas_bp.route('/<uuid:empresa_id>', methods=['DELETE'])
def delete_empresa(empresa_id: uuid.UUID):
    """
    API endpoint to delete a company from the system.
    """
    logger.info(f"Received request to delete company ID: {empresa_id}")
    # db_session = db.session # Acceder a la sesión
    try:
        deleted = empresa_service.delete_empresa(db.session, empresa_id) # <<<<<<<<<<<< PASAR db.session
        if deleted:
            return jsonify({"message": "Empresa eliminada correctamente."}), 204 
        else:
            return jsonify({"message": "Empresa no encontrada o no se pudo eliminar (puede tener registros asociados)."}), 404
    except Exception as e:
        logger.exception(f"Error deleting company ID {empresa_id}: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar la empresa."}), 500
    # No hay db.close() aquí.