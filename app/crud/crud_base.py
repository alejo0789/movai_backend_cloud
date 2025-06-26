# app/crud/crud_base.py
import uuid 
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from datetime import datetime, date 

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models_db.cloud_database_models import Base as DeclarativeBaseModel 

# Define un tipo genérico para el modelo de base de datos
ModelType = TypeVar("ModelType", bound=DeclarativeBaseModel)

class CRUDBase(Generic[ModelType]):
    """
    Clase base para las operaciones CRUD (Crear, Leer, Actualizar, Borrar)
    con la base de datos SQLAlchemy.
    """
    def __init__(self, model: Type[ModelType]):
        """
        Args:
            model (Type[ModelType]): El modelo de SQLAlchemy al que se aplicará el CRUD.
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Obtiene un registro por su ID principal.
        """
        if hasattr(self.model, 'id') and isinstance(id, str) and hasattr(self.model.id.type, 'python_type') and self.model.id.type.python_type == uuid.UUID:
            try:
                id = uuid.UUID(id)
            except ValueError:
                return None 
        
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Obtiene múltiples registros con paginación.
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def get_multi_by_ids(self, db: Session, ids: List[uuid.UUID]) -> List[ModelType]:
        """
        Obtiene múltiples registros por una lista de sus IDs principales.
        """
        # Asegurarse de que los IDs en la lista sean del tipo correcto si el modelo.id es UUID
        processed_ids = []
        if hasattr(self.model, 'id') and hasattr(self.model.id.type, 'python_type') and self.model.id.type.python_type == uuid.UUID:
            for _id in ids:
                if isinstance(_id, str):
                    try: processed_ids.append(uuid.UUID(_id))
                    except ValueError: pass # Ignorar IDs inválidos
                else: processed_ids.append(_id)
        else:
            processed_ids = ids # Si el ID no es UUID, se usa la lista tal cual

        if not processed_ids:
            return [] # No hay IDs válidos para buscar

        return db.query(self.model).filter(self.model.id.in_(processed_ids)).all()


    def create(self, db: Session, obj_in: Dict[str, Any]) -> ModelType:
        """
        Crea un nuevo registro en la base de datos.
        obj_in debe ser un diccionario con los datos del nuevo registro.
        """
        processed_data = self._process_data_for_model(obj_in, self.model)
        
        db_obj = self.model(**processed_data)  
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelType, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """
        Actualiza un registro existente en la base de datos.
        db_obj es la instancia del modelo a actualizar.
        obj_in es un diccionario con los campos a actualizar.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else: 
            update_data = obj_in.dict(exclude_unset=True) 

        processed_update_data = self._process_data_for_model(update_data, self.model)
        
        for field in processed_update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, processed_update_data[field])

        db.add(db_obj) 
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Elimina un registro por su ID principal.
        """
        obj = self.get(db, id) 
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_by_attribute(self, db: Session, attribute: str, value: Any) -> Optional[ModelType]:
        """
        Obtiene un registro por un atributo específico y su valor.
        """
        column = getattr(self.model, attribute, None)
        if column is not None and hasattr(column.type, 'python_type') and column.type.python_type == uuid.UUID and isinstance(value, str):
            try:
                value = uuid.UUID(value)
            except ValueError:
                return None 
        
        return db.query(self.model).filter(getattr(self.model, attribute) == value).first()

    def create_or_update(self, db: Session, obj_data: Dict[str, Any], unique_field: str = 'id') -> ModelType:
        """
        Crea un registro si no existe o lo actualiza si ya existe,
        basándose en un campo único (por defecto 'id').
        Ideal para sincronización de datos Edge-Cloud.
        """
        unique_value = obj_data.get(unique_field)
        if not unique_value:
            raise ValueError(f"El campo único '{unique_field}' es requerido para create_or_update.")

        column = getattr(self.model, unique_field, None)
        if column is not None and hasattr(column.type, 'python_type') and column.type.python_type == uuid.UUID and isinstance(unique_value, str):
            try:
                unique_value = uuid.UUID(unique_value)
            except ValueError:
                raise ValueError(f"El valor para el campo único '{unique_field}' no es un UUID válido.")

        existing_obj = self.get_by_attribute(db, unique_field, unique_value)

        if existing_obj:
            update_data = {k: v for k, v in obj_data.items() if k != unique_field}
            updated_obj = self.update(db, existing_obj, update_data)
            return updated_obj
        else:
            obj_data[unique_field] = unique_value 
            try:
                new_obj = self.create(db, obj_data)
                return new_obj
            except IntegrityError as e:
                db.rollback()
                raise ValueError(f"Error de integridad al crear el objeto: {e.orig}")

    def _process_data_for_model(self, data: Dict[str, Any], model_class: Type[ModelType]) -> Dict[str, Any]:
        """
        Función auxiliar para procesar datos de entrada (dict) y convertir
        UUIDs y fechas/horas de string a los tipos de Python correspondientes
        basándose en las columnas del modelo.
        """
        processed_data = data.copy()
        for col_name, column in model_class.__table__.columns.items():
            if col_name in processed_data and isinstance(processed_data[col_name], str):
                if hasattr(column.type, 'python_type'):
                    if column.type.python_type == uuid.UUID:
                        try:
                            processed_data[col_name] = uuid.UUID(processed_data[col_name])
                        except ValueError:
                            processed_data[col_name] = None 
                    elif column.type.python_type == datetime:
                        try:
                            processed_data[col_name] = datetime.fromisoformat(processed_data[col_name])
                        except ValueError:
                            processed_data[col_name] = None
                    elif column.type.python_type == date:
                        try:
                            processed_data[col_name] = datetime.fromisoformat(processed_data[col_name]).date()
                        except ValueError:
                            processed_data[col_name] = None
        return processed_data