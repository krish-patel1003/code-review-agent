from typing import Dict, List
from dataclasses import dataclass
from app.services import GithubService
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from langchain_chroma import Chroma
import google.generativeai as genai
from app.services.github_integration import PRDetails

@dataclass
class RepoContext:
    repo_url: str
    files: List[str]
    tree_structure: str
    file_contents: List[Dict]


class CodeReviewAgent:
    def __init__(self, github_service: GithubService, api_key: str):
        self.github_client = github_service
        try:
            genai.configure(api_key=api_key)

            self.llm = GoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=api_key,
                temperature=0.3,
                top_k=40,
                top_p=0.95,
                max_output_tokens=2048,
            )

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key,
                task_type="retrieval_document",
            )

        except Exception as e:
            raise Exception(f"Failed to initialize Gemini API: {e}")

        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

    def setup_repo_context(self, repo_url: str) -> RepoContext:
        tree_structure, file_paths = self.github_client.get_tree_strucutre_and_file_paths(repo_url)
        texts = []
        metadatas = []
        file_contents = []

        for file_path in file_paths:
            file_content = self.github_client.get_file_content(repo_url, file_path, ref="main")
            if file_content:
                file_contents.append({"filename": file_path, "content": file_content})
                chunks = self.text_splitter.split_text(file_content)
                texts.extend(chunks)
                metadatas.extend([{"file": file_path, "type": "content"}] * len(chunks))

        texts.append(tree_structure)
        metadatas.append({"type": "structure"})

        if self.vector_store is None:
            self.vector_store = Chroma(collection_name="repo_context", embedding_function=self.embeddings)

        self.vector_store.add_texts(texts=texts, metadatas=metadatas)

        return RepoContext(repo_url=repo_url, files=file_paths, tree_structure=tree_structure, file_contents=file_contents)

    def review_changes(self, pr_details: PRDetails, repo_context: RepoContext) -> str:
        review_template = """
You are an expert code reviewer. Please review the following code changes:

Context:
Repository Structure: {repo_structure}

Relevant Repository Content:
{relevant_context}

Files changed: {files_changed}

Changes:
{diff_content}

Consider:
1. Code quality and adherence to best practices
2. Potential bugs or edge cases
3. Performance optimizations
4. Readability and maintainability
5. Any security concerns

Provide a detailed review with specific suggestions for improvements. Format your response as
a json with an object files that has list of files that has issues, each sub object in it should have these attributes:
filename,
issue_type,
line_number_of_issue,
issue_description,
suggestions

and at last last object in the json should be a summary of having attributes total_files_changed, total_issues, and critical_issues
        """

        prompt = ChatPromptTemplate.from_template(review_template)
        diff_text = "\n".join([f"=== {file.filename} ===\n{file.content}" for file in pr_details.files])
        files_changed = ", ".join([file.filename for file in pr_details.files])

        relevant_docs = []
        for file in pr_details.files:
            results = self.vector_store.similarity_search(file.filename, k=2, filter={"type": "content"})
            relevant_docs.extend(results)

        relevant_context = "\n".join([doc.page_content for doc in relevant_docs])

        final_prompt = prompt.invoke({
            "repo_structure": repo_context.tree_structure,
            "relevant_context": relevant_context,
            "files_changed": files_changed,
            "diff_content": diff_text
        })

        review = self.llm.invoke(final_prompt)
        return review

    @staticmethod
    def parse_review_response(review: str) -> Dict:
        review = review.strip("```").lstrip("json\n").rstrip("\n")
        return eval(review)
