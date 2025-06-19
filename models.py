from pydantic import BaseModel, Field
from typing import List, Optional

class WorkExperience(BaseModel):
    role: str = Field(description="The job title or role.")
    company: str = Field(description="The name of the company.")
    duration: Optional[str] = Field(description="The duration of employment (e.g., 'Jan 2020 - Dec 2022').")
    responsibilities: List[str] = Field(description="A list of key responsibilities or achievements.")

class EducationDetail(BaseModel):
    degree: str = Field(description="The degree obtained.")
    institution: str = Field(description="The name of the institution.")
    graduation_date: Optional[str] = Field(description="The graduation date or expected graduation date.")

class ResumeDetails(BaseModel):
    summary: Optional[str] = Field(description="A brief summary or objective from the resume.")
    work_experiences: List[WorkExperience] = Field(description="A list of work experiences.")
    skills: List[str] = Field(description="A list of skills (technical and soft).")
    education_details: List[EducationDetail] = Field(description="A list of educational qualifications.")
    projects_or_certifications: Optional[List[str]] = Field(description="A list of projects or certifications, if any.")

class JobDescriptionDetails(BaseModel):
    job_title: Optional[str] = Field(description="The title of the job position.")
    key_responsibilities: List[str] = Field(description="A list of the main responsibilities for the role.")
    must_have_skills: List[str] = Field(description="A list of essential skills required for the job.")
    preferred_skills: Optional[List[str]] = Field(description="A list of preferred or desired skills.")
    required_experience_years: Optional[str] = Field(description="The number of years of experience required (e.g., '3-5 years').")
    educational_requirements: Optional[List[str]] = Field(description="A list of educational qualifications needed.")
    company_culture_values: Optional[List[str]] = Field(description="Any mentioned company culture points or values.")