from typing import List, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    # Cada grupo lista os ids ("Nome <email>") de identidades que são a mesma pessoa.
    groups: List[List[str]] = Field(default_factory=list)
