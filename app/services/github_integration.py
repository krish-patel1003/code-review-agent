from dataclasses import dataclass
from typing import List, Optional, Tuple
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.ContentFile import ContentFile
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

    
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        path = urlparse(repo_url).path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError("Invalid Github repo url")

        return parts[0], parts[1]


    def get_default_branch(self, repo_url: str) -> str:
        repo = self._get_repo(repo_url=repo_url)
        return repo.default_branch
 
    
    def _get_repo(self, repo_url: str) -> Repository:
        owner, repo_name = self._parse_repo_url(repo_url=repo_url)
        return self.client.get_repo(f"{owner}/{repo_name}")


    def _get_repo_content(self, repo_url: str, path: str = ""):
        repo = self._get_repo(repo_url=repo_url)
        contents = repo.get_contents(path)
        return contents

    def _build_tree_structure(
        self, repo: Repository, contents: list[ContentFile] | ContentFile, tree_structure: str, file_paths: list,  level: int):

        while contents:
            file_content = contents.pop(0)
            current_path = file_content.path

            # Add proper indentation based on the level
            indentation = "    " * level
            if file_content.type == "dir":
                tree_structure += f"{indentation}{file_content.name}/\n"
                new_contents = repo.get_contents(file_content.path)
                # Recursively call _traverse with an increased level
                tree_structure = self._build_tree_structure(
                    repo=repo, contents=new_contents, file_paths=file_paths, tree_structure=tree_structure, level=level + 1)
            else:
                tree_structure += f"{indentation}{file_content.name}\n"
                file_paths.append(current_path)

        return tree_structure

    def get_tree_strucutre_and_file_paths(self, repo_url: str):
        
        repo = self._get_repo(repo_url=repo_url)
        contents = self._get_repo_content(repo_url=repo_url)

        tree_structure = ""
        file_paths = []

        tree_structure = self._build_tree_structure(repo=repo, contents=contents, tree_structure=tree_structure, file_paths=file_paths, level=0)
        return tree_structure, file_paths

    
    def get_pr_details(self, repo_url: str, pr_number: int) -> PRDetails:

        tree_str, file_paths = self.get_tree_strucutre_and_file_paths(repo_url=repo_url)

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
            repo = self._get_repo(repo_url)
            content_file = repo.get_contents(file_path, ref=ref)
            if isinstance(content_file, (list, tuple)):
                return None
            return base64.b64decode(content_file.content).decode('utf-8')
        except Exception as e:
            print(f"Error fetching file content: {e}")
            return None


    def get_github_repo_complete_data(self, repo_url: str) -> List[dict]:
        directory_tree, file_paths = self.get_tree_strucutre_and_file_paths(repo_url=repo_url)

        contents = []

        for path in file_paths:
            branch = self.get_default_branch(repo_url=repo_url)
            file_content = self.get_file_content(repo_url=repo_url, file_path=path, ref= branch)
            filetype = ""

            if ("." in path):
                filetype = path.split(".")[-1]

            contents.append({
                "filename": path,
                "filetype": filetype,
                "content": file_content
            })

        return directory_tree, file_paths, contents

    def get_diff_sections(self, repo_url: str, pr_number: int) -> List[str]:
        try:
            pr_details = self.get_pr_details(repo_url=repo_url, pr_number=pr_number)
            return [file.patch for file in pr_details.files if file.patch]
        except Exception as e:
            raise Exception(f"Error fetching diff sections: {e}")

    
    def get_commit_history(self, repo_url: str, branch: Optional[str] = None) -> List[dict]:
        try:
            repo = self._get_repo(repo_url=repo_url)
            branch = branch or repo.default_branch
            commits = repo.get_commits(sha=branch)
            return [
                {
                    "sha": commit.sha,
                    "author": commit.commit.author.name,
                    "message": commit.commit.message,
                    "date": commit.commit.author.date.isoformat(),
                }
                for commit in commits
            ]
        except Exception as e:
            raise Exception(f"Error fetching commit history: {e}")

    
    def get_pr_statistics(self, repo_url: str, pr_number: int) -> dict:
        try:
            pr_details = self.get_pr_details(repo_url=repo_url, pr_number=pr_number)
            total_additions = sum(file.additions for file in pr_details.files)
            total_deletions = sum(file.deletions for file in pr_details.files)
            total_changes = sum(file.changes for file in pr_details.files)
            return {
                "total_files": len(pr_details.files),
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "total_changes": total_changes,
            }
        except Exception as e:
            raise Exception(f"Error fetching PR statistics: {e}")


# if __name__ == "__main__":

#     repo_url = "https://github.com/krish-patel1003/RMS"
#     client = GithubService("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")
#     tree, file_paths = client.get_tree_strucutre_and_file_paths(repo_url=repo_url)
#     print(file_paths)
#     result = client.retrieve_github_repo_all_content(repo_url=repo_url)
#     print(result)