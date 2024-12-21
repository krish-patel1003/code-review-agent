from celery.signals import task_success
from app.config import get_code_review_agent, get_github_service, get_celery_app, get_cache_client
from app.db import save_analysis

celery_app = get_celery_app()

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
            "repo_url": repo_context.repo_url,
            "pr_number": pr_number,
            "pr_review": parsed_review
        }
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=3)


@task_success.connect(sender=full_review_workflow_task)
def save_analysis_on_success(sender, result=None, **kwargs):
    task_id = sender.request.id.__str__()
    repo_url = result.get("repo_url")
    pr_number = result.get("pr_number")

    cache_client = get_cache_client()
    cache_client.set(task_id, str(result))
    save_analysis(task_id, repo_url, pr_number, str(result))