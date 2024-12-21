from sqlalchemy.exc import IntegrityError
from app.db.database import SessionLocal
from app.db.models import AnalysisResult

def get_analysis_by_repo_pr(repo_url: str, pr_number: int):
    """Fetch analysis entry by repo_url and pr_number."""
    with SessionLocal() as session:
        query = session.query(AnalysisResult).filter(
            AnalysisResult.repo_url == repo_url,
            AnalysisResult.pr_number == pr_number
        )
        return query.first()

def save_analysis(task_id: str, repo_url: str, pr_number: int, result: dict):
    """Save analysis entry to the database."""
    with SessionLocal() as session:
        analysis = AnalysisResult(task_id=task_id, repo_url=repo_url, pr_number=pr_number, result=result)
        session.add(analysis)
        session.commit()
        return analysis

def get_analysis_by_id(task_id: str):
    """Fetch analysis entry by task_id."""
    print("in get_analysis_results")
    print("task_id in analysis func:\t", task_id)
    with SessionLocal() as session:
        obj = session.get(AnalysisResult, task_id)
        print("OBJ:\t", obj)
        query = session.query(AnalysisResult).filter(AnalysisResult.task_id == task_id)
        return query.first()