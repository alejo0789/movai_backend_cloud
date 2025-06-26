# app/services/empresa_service.py
import logging
from typing import Optional, Dict, Any, List
import uuid # Needed for UUID types

from sqlalchemy.orm import Session # For type hinting the database session

# Import the specific CRUD operations for Empresa
from app.crud.crud_empresa import empresa_crud
# Import the Empresa model to be able to return typed objects
from app.models_db.cloud_database_models import Empresa

# Setup logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class EmpresaService:
    """
    Service layer for managing Empresa (Company) related business logic.
    Interacts with the CRUD layer to perform database operations.
    """

    def register_new_empresa(self, db: Session, empresa_data: Dict[str, Any]) -> Optional[Empresa]:
        """
        Registers a new company in the system.
        Performs business validation like checking for duplicate NIT.

        Args:
            db (Session): The database session.
            empresa_data (Dict[str, Any]): Dictionary containing company data (e.g., name, NIT).

        Returns:
            Optional[Empresa]: The newly created Empresa object, or None if validation fails.
        """
        logger.info(f"Attempting to register new company: {empresa_data.get('nombre_empresa')}")

        # Basic validation: Check for existing NIT to prevent duplicates
        # The unique constraint in the DB will also catch this, but checking beforehand
        # allows for a more graceful error message.
        existing_empresa = empresa_crud.get_by_nit(db, empresa_data.get('nit'))
        if existing_empresa:
            logger.warning(f"Company with NIT '{empresa_data.get('nit')}' already exists.")
            # In a real API, you'd raise an HTTPException or return a specific error code
            return None 
        
        try:
            # Create the company using the CRUD operation
            new_empresa = empresa_crud.create(db, empresa_data)
            logger.info(f"Company '{new_empresa.nombre_empresa}' (ID: {new_empresa.id}) registered successfully.")
            return new_empresa
        except Exception as e:
            logger.error(f"Error registering company '{empresa_data.get('nombre_empresa')}': {e}", exc_info=True)
            db.rollback() # Rollback transaction in case of error
            return None

    def get_empresa_details(self, db: Session, empresa_id: uuid.UUID) -> Optional[Empresa]:
        """
        Retrieves details of a specific company by its ID.
        """
        logger.info(f"Fetching details for company ID: {empresa_id}")
        empresa = empresa_crud.get(db, empresa_id)
        if not empresa:
            logger.warning(f"Company with ID '{empresa_id}' not found.")
        return empresa

    def get_all_empresas(self, db: Session, skip: int = 0, limit: int = 100) -> List[Empresa]:
        """
        Retrieves a list of all companies with pagination.
        """
        logger.info(f"Fetching all companies (skip={skip}, limit={limit}).")
        return empresa_crud.get_multi(db, skip=skip, limit=limit)
    
    def update_empresa_details(self, db: Session, empresa_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[Empresa]:
        """
        Updates details for an existing company.
        """
        logger.info(f"Attempting to update company ID: {empresa_id}")
        empresa = empresa_crud.get(db, empresa_id)
        if not empresa:
            logger.warning(f"Cannot update: Company with ID '{empresa_id}' not found.")
            return None
        
        # You could add more complex validation here (e.g., prevent changing NIT if not allowed)
        
        try:
            updated_empresa = empresa_crud.update(db, empresa, updates)
            logger.info(f"Company '{empresa.nombre_empresa}' (ID: {empresa_id}) updated successfully.")
            return updated_empresa
        except Exception as e:
            logger.error(f"Error updating company ID '{empresa_id}': {e}", exc_info=True)
            db.rollback()
            return None

    def delete_empresa(self, db: Session, empresa_id: uuid.UUID) -> bool:
        """
        Deletes a company from the system.
        Considers cascading deletions or soft deletes for related data (buses, conductors).
        """
        logger.info(f"Attempting to delete company ID: {empresa_id}")
        # In a real system, you'd implement soft delete or carefully handle
        # related records (e.g., set buses/conductors to inactive or reassign them).
        # For now, we'll use a hard delete from CRUD, which will likely fail
        # if there are related records due to foreign key constraints.
        
        # Consider checking for related records before deleting
        # if empresa.buses or empresa.conductores: # Assuming relationships are loaded
        #     logger.warning("Cannot delete company with associated buses or conductors.")
        #     return False

        try:
            deleted_empresa = empresa_crud.remove(db, empresa_id)
            if deleted_empresa:
                logger.info(f"Company ID '{empresa_id}' deleted successfully.")
                return True
            else:
                logger.warning(f"Company with ID '{empresa_id}' not found for deletion.")
                return False
        except Exception as e:
            logger.error(f"Error deleting company ID '{empresa_id}': {e}", exc_info=True)
            db.rollback()
            return False

# Create an instance of the EmpresaService to be used by the API endpoints.
empresa_service = EmpresaService()