from pydantic import BaseModel, Field

class RequestModel(BaseModel):
    query:str
    section: str = Field(default="rfp_documents", description="the section to query data from")