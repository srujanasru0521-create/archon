import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

class LayerConfig(BaseModel):
    name: str
    path: str

class ArchonConfig(BaseModel):
    layers: List[LayerConfig] = []
    constraints: List[str] = []

def load_config(workspace_root: Path) -> ArchonConfig:
    config_path = workspace_root / "archon.yaml"
    if not config_path.exists():
        return ArchonConfig()
    
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
        
    if not data:
        return ArchonConfig()
        
    return ArchonConfig(**data)
