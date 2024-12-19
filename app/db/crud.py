from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from app.db.models import AnalysisResult


async def save_analysis(task_id: str, repo_url: str, result: dict):

    async with SessionLocal() as session:
        analysis = AnalysisResult(task_id=task_id, repo_url=repo_url, result=result)
        session.add(analysis)
        await session.commit()


async def get_analysis_by_id(task_id: str):

    async with SessionLocal() as session:
        query = select(AnalysisResult).where(AnalysisResult.task_id == task_id)
        result = await session.execute(query)
        return result.scalars().first()

    