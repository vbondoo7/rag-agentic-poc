# ai_agents/models.py
from typing import List, Optional
from pydantic import BaseModel, Field

class ComponentModel(BaseModel):
    name: str
    impact: str
    level: str
    tshirt_size: str
    justification: str
    sources: Optional[List[str]] = []

class ImpactModel(BaseModel):
    intent: str = "impact"
    components: List[ComponentModel] = []
    summary: Optional[str] = ""

class ModuleModel(BaseModel):
    name: str
    purpose: Optional[str] = ""
    pattern: Optional[str] = ""
    data_flow: Optional[List[str]] = []
    risks: Optional[List[str]] = []
    tshirt_size: Optional[str] = ""

class SolutionModel(BaseModel):
    modules: List[ModuleModel] = []

class BlueprintModel(BaseModel):
    intent: str = "blueprint"
    solution: SolutionModel = SolutionModel()
    recommendations: Optional[List[str]] = []
    summary: Optional[str] = ""
