from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator):
        return {"type": "string"}


class ScanRequest(BaseModel):
    target_url: str


class ScanUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ScanResponse(BaseModel):
    id: str = Field(alias="_id")
    target_url: str
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)
