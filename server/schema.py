from pydantic import BaseModel
import json
from typing import List, Dict, Any

    
from typing import List, Dict
from pydantic import BaseModel
class ImportRequest(BaseModel):
    adminname: str
    encoding: str
    filename: str
    data: List[Dict] 
    
    
class ExportRequest(BaseModel):
    adminname: str
    filename: str
    mode_export: str
    encoding: str
    mode_file: str
    
    