from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator):
        return {"type": "string"}   
    
class ScanRequest(BaseModel):
    target: str

class ScanResponse(BaseModel):        
    id: str = Field(alias="_id")
    target_url: str
    status: str = "pending"
    results: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}