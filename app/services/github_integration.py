from dataclasses import dataclass
from typing import List, Optional
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
import base64
from urllib.parse import urlparse


@dataclass
class PRFile:
    filename: str
    status: str # added, removed, modified
    additions: int
    deletions: int
    changes: int
    patch: Optional[str]
    content: Optional[str]


@dataclass
class PRDetails:
    title: str
    description: str
    state: str
    files: List[PRFile]
    diff: str


class GithubService:


    def __init__(self, github_token: Optional[str] = None):
        self.client = Github(github_token) if github_token else Github()

    
    def _parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        path = urlparse(repo_url).path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError("Invalid Github repo url")

        return parts[0], parts[1]

    
    def _get_repo(self, repo_url: str) -> Repository:
        owner, repo_name = self._parse_repo_url(repo_url=repo_url)
        return self.client.get_repo(f"{owner}/{repo_name}")

    
    def get_pr_details(self, repo_url: str, pr_number: int) -> PRDetails:

        try:
            repo = self._get_repo(repo_url=repo_url)
            pr: PullRequest = repo.get_pull(number=pr_number)

            files = []
            for file in pr.get_files():

                content = None
                if file.status != 'removed':
                    try:
                        file_content = repo.get_contents(file.filename, ref=pr.head.sha)
                        if isinstance(file_content, (list, tuple)):
                            continue
                        content = base64.b64decode(file_content.content).decode('utf-8')
                    except Exception as e:
                        print(f"Error fetching content for {file.filename}: {e}")

                files.append(PRFile(
                    filename=file.filename,
                    status=file.status,
                    additions=file.additions,
                    deletions=file.contents_url,
                    changes=file.changes,
                    patch=file.patch,
                    content=content
                ))


            return PRDetails(
                title=pr.title,
                description=pr.body or "",
                state=pr.state,
                files=files,
                diff=pr.diff_url
            )

        except Exception as e:
            raise Exception(f"Error fetching PR Details: {e}")

    
    def get_file_content(self, repo_url: str, file_path: str, ref: str) -> Optional[str]:

        try:
            repo = self._get_repository(repo_url)
            content_file = repo.get_contents(file_path, ref=ref)
            if isinstance(content_file, (list, tuple)):
                return None
            return base64.b64decode(content_file.content).decode('utf-8')
        except Exception as e:
            print(f"Error fetching file content: {e}")
            return None