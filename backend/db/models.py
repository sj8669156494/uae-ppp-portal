import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Text, Enum as SAEnum, Index,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class SectorEnum(str, enum.Enum):
    Transport = "Transport"
    Energy = "Energy"
    Water = "Water"
    Healthcare = "Healthcare"
    Education = "Education"
    Social = "Social"
    Infrastructure = "Infrastructure"
    Environment = "Environment"
    Other = "Other"


class EmirateEnum(str, enum.Enum):
    Abu_Dhabi = "Abu Dhabi"
    Dubai = "Dubai"
    Sharjah = "Sharjah"
    Ras_Al_Khaimah = "Ras Al Khaimah"
    Fujairah = "Fujairah"
    Ajman = "Ajman"
    Umm_Al_Quwain = "Umm Al Quwain"
    Multiple = "Multiple"
    Federal = "Federal"


class StatusEnum(str, enum.Enum):
    Planned = "Planned"
    Tendering = "Tendering"
    Under_Execution = "Under Execution"
    Complete = "Complete"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    sector = Column(SAEnum(SectorEnum), nullable=False)
    emirate = Column(SAEnum(EmirateEnum), nullable=False)
    owner = Column(String(500), nullable=False)
    contract_value_aed = Column(Float, nullable=True)
    status = Column(SAEnum(StatusEnum), nullable=False)
    contractors = Column(String(1000), nullable=True)
    expected_completion_year = Column(Integer, nullable=True)
    source_url = Column(String(2000), nullable=False)
    source_name = Column(String(200), nullable=False)
    raw_text = Column(Text, nullable=True)
    extraction_confidence = Column(Float, default=1.0)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    notes = Column(Text, nullable=True)

    # V2 extended fields
    description = Column(Text, nullable=True)
    sub_sector = Column(String(200), nullable=True)
    responsible_entity = Column(String(500), nullable=True)
    project_type = Column(String(200), nullable=True)
    mode_of_implementation = Column(String(200), nullable=True)
    ppp_type = Column(String(200), nullable=True)
    ppp_model = Column(String(200), nullable=True)
    requirements = Column(Text, nullable=True)
    start_date = Column(String(20), nullable=True)
    tender_end_date = Column(String(20), nullable=True)
    news_link = Column(String(2000), nullable=True)
    ministry_link = Column(String(2000), nullable=True)
    contact_details = Column(String(1000), nullable=True)

    __table_args__ = (
        Index("ix_projects_sector", "sector"),
        Index("ix_projects_emirate", "emirate"),
        Index("ix_projects_status", "status"),
        Index("ix_projects_is_duplicate", "is_duplicate"),
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r} sector={self.sector}>"
