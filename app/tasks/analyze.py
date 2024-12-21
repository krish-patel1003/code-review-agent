from app.config import celery_app
from app.config import get_code_review_agent, get_github_service

@celery_app.task(bind=True)
def full_review_workflow_task(self, repo_url: str, pr_number: int):
    try:
        github_service = get_github_service()
        code_review_agent = get_code_review_agent()

        repo_context = code_review_agent.setup_repo_context(repo_url)
        pr_details = github_service.get_pr_details(repo_url=repo_url, pr_number=pr_number)
        review_response = code_review_agent.review_changes(pr_details=pr_details, repo_context=repo_context)
        parsed_review = code_review_agent.parse_review_response(review_response)

        return {
            "repo_context": {"tree_structure": repo_context.tree_structure, "files": repo_context.files},
            "pr_review": parsed_review
        }
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=3)
