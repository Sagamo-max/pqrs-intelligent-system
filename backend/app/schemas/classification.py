from pydantic import BaseModel, Field
from typing import Literal

class PQRSClassification(BaseModel):
    tipo_pqrs: Literal["Peticion", "Queja", "Reclamo", "Sugerencia"] = Field(
        description="Clasificación principal según la intención del usuario."
    )
    prioridad: Literal["Alta", "Media", "Baja"] = Field(
        description="Nivel de urgencia. Reclamos suelen ser Alta, sugerencias Baja."
    )
    area_responsable: str = Field(
        description="Área de la empresa que debe resolver la solicitud (ej. Servicio al Cliente, Facturación, Soporte Técnico)."
    )
    justificacion_decision: str = Field(
        description="Explicación obligatoria y concisa de por qué se asignó este tipo, prioridad y área. Sirve para auditoría."
    )