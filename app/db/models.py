from sqlalchemy import Column, String, JSON, UniqueConstraint, Integer
from app.db.database import Base

class AnalysisResult(Base):

    __tablename__= "analysis_results"

    task_id = Column(String, primary_key=True, index=True)
    repo_url = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=False)
    result = Column(JSON, nullable=False)