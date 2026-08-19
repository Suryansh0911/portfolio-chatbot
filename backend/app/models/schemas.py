from pydantic import BaseModel, Field
from typing import List

class PersonalInfo(BaseModel):
    name: str=""
    email: str=""
    phone: str=""
    location: str=""
    linkedin: str=""
    github: str=""

class Education(BaseModel):
    degree: str = ""
    institution: str = ""
    location: str = ""
    start_year: str = ""
    end_year: str = ""


class Experience(BaseModel):
    company: str = ""
    role: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: List[str] = []


class Project(BaseModel):
    name: str = ""
    description: str = ""
    technologies: List[str] = []
    github: str = ""


class Portfolio(BaseModel):
    personal: PersonalInfo
    education: List[Education] = []
    experience: List[Experience] = []
    projects: List[Project] = []
    skills: List[str] = []
    achievements: List[str] = []


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    conversation_id: str = Field(
        default="default",
        min_length=1,
        max_length=100
    )


class ChatResponse(BaseModel):
    conversation_id: str
    response: str