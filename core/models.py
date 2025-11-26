from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import itertools

_id_counters = {
    "cj": itertools.count(1),
    "cp": itertools.count(1),
}

def next_cj_id():
    return f"CJ_{next(_id_counters['cj']):04d}"

def next_cp_id():
    return f"CP_{next(_id_counters['cp']):04d}"

class MateriaPrima(BaseModel):
    mp: str
    quantidade: float
    unidade: str  # "UN" or "KG"
    rendimento: float  # percentual (e.g., 95 or 100)

    @validator("unidade")
    def unidade_valida(cls, v):
        if v not in ("UN", "KG"):
            raise ValueError("unidade must be 'UN' or 'KG'")
        return v

    @validator("rendimento")
    def rendimento_range(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("rendimento must be between 0 and 100")
        return v

class Componente(BaseModel):
    id: str = Field(default_factory=next_cp_id)
    nome: str
    quantidade: int = 1
    materias: List[MateriaPrima] = []

    def peso_kg(self) -> float:
        # Peso calculado: soma das MPs em KG (se unidade=KG), UN não soma peso (requer política)
        total = 0.0
        for m in self.materias:
            if m.unidade == "KG":
                total += float(m.quantidade)
        return total

class Conjunto(BaseModel):
    id: str = Field(default_factory=next_cj_id)
    nome: str
    cor: str
    componentes: List[Componente] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    autor: Optional[str] = None

    def peso_kg(self) -> float:
        return sum(c.peso_kg() for c in self.componentes)

class Projeto(BaseModel):
    projeto_nome: str
    conjuntos: List[Conjunto] = []