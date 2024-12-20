from typing import Dict, List, Optional
from pathlib import Path
import os
from dataclasses import dataclass
from app.services import GithubService
from fastapi import Depends
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import Graph, StateGraph
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from langchain_chroma import Chroma
import chromadb
import google.generativeai as genai

@dataclass
class RepoContext:
    repo_url: str
    files: List[str]
    tree_structure: str
    file_contents: List[Dict]

@dataclass
class PRDetails:
    files_changed: List[str]
    diff_content: Dict[str, str]
    additions: int
    deletions: int

class CodeReviewAgent:
    def __init__(self, repo_url: str, github_service: GithubService):
        self.github_client= github_service
        self.repo_url = repo_url
        try:
            # Configure Gemini
            api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCDL8mcL3MZdO1ikRbogJ1wTeBeaBLFhAQ")
            genai.configure(api_key=api_key)
            
            # Initialize LLM
            self.llm = GoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=api_key,
                temperature=0.3,
                top_k=40,
                top_p=0.95,
                max_output_tokens=2048,
            )
            
            # Initialize embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key,
                task_type="retrieval_document",
            )
            
            # Test connection
            self.llm.invoke("test connection")
            
        except Exception as e:
            raise GeminiAPIError(
                f"Failed to initialize Gemini API: {str(e)}\n"
                "Please ensure you have:\n"
                "1. A valid Google API key\n"
                "2. Installed required packages: pip install google-generative-ai langchain-google-genai"
            )
            
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        
    def setup_repo_context(self) -> RepoContext:
        """Initialize repository context and store in vector database"""       
        # Get repository structure      

        tree_structure, file_paths, file_contents = self.github_client.get_github_repo_complete_data(repo_url=self.repo_url)
        
        # Store in vector database
        texts = []
        metadatas = []
        
        for file in file_contents:
            chunks = self.text_splitter.split_text(file["content"])
            texts.extend(chunks)
            metadatas.extend([{"file": file["filename"], "filetype": file["filetype"], "type": "content"}] * len(chunks))
        
        # Add repository structure
        tree_text = "\n".join(tree_structure)
        texts.append(tree_text)
        metadatas.append({"type": "structure"})
        
        # Create or get vector store
        if self.vector_store is None:
            self.vector_store = Chroma(
                collection_name="repo_context",
                embedding_function=self.embeddings
            )
            
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)

        repo_context = RepoContext(
            repo_url=self.repo_url,
            files=file_paths,
            tree_structure="\n".join(tree_structure),
            file_contents=file_contents
        )
        
        print(repo_context)

        return repo_context
    
    def get_pr_details(self, pr_branch: str, base_branch: str = "main") -> PRDetails:
        """Extract information about changes in the PR"""
        # Get diff between branches
        diff_index = repo.commit(base_branch).diff(repo.commit(pr_branch))
        
        files_changed = []
        diff_content = {}
        additions = 0
        deletions = 0
        
        for diff_item in diff_index:
            file_path = diff_item.a_path
            files_changed.append(file_path)
            diff_content[file_path] = diff_item.diff.decode('utf-8')
            
            # Count additions and deletions
            for line in diff_content[file_path].split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    additions += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deletions += 1
        
        return PRDetails(
            files_changed=files_changed,
            diff_content=diff_content,
            additions=additions,
            deletions=deletions
        )
    
#     def review_changes(self, pr_details: PRDetails) -> str:
#         """Review code changes using the LLM"""
#         review_template = """You are an expert code reviewer. Please review the following code changes:

# Context:
# Files changed: {files_changed}
# Total additions: {additions}
# Total deletions: {deletions}

# Changes:
# {diff_content}

# Consider:
# 1. Code quality and adherence to best practices
# 2. Potential bugs or edge cases
# 3. Performance optimizations
# 4. Readability and maintainability
# 5. Any security concerns

# Provide a detailed review with specific suggestions for improvements. Format your response as:
# - Summary of changes
# - Key concerns (if any)
# - Specific recommendations
# - Positive aspects
# """
        
#         prompt = ChatPromptTemplate.from_template(review_template)
        
#         # Get relevant context from vector store
#         relevant_docs = []
#         for file in pr_details.files_changed:
#             results = self.vector_store.similarity_search(
#                 file,
#                 k=2,
#                 filter={"type": "content"}
#             )
#             relevant_docs.extend(results)
        
#         # Combine diff content
#         diff_text = "\n".join([
#             f"=== {file} ===\n{content}\n"
#             for file, content in pr_details.diff_content.items()
#         ])
        
#         # Generate review
#         review = self.llm.predict(
#             prompt.format(
#                 files_changed=", ".join(pr_details.files_changed),
#                 additions=pr_details.additions,
#                 deletions=pr_details.deletions,
#                 diff_content=diff_text
#             )
#         )
        
#         return review

# def create_review_workflow() -> Graph:
#     """Create a LangGraph workflow for the code review process"""
#     workflow = StateGraph(GraphStore())
    
#     # Define nodes
#     workflow.add_node("setup_context", lambda x: x["agent"].setup_repo_context())
#     workflow.add_node("get_pr_details", lambda x: x["agent"].get_pr_details(x["pr_branch"]))
#     workflow.add_node("review_code", lambda x: x["agent"].review_changes(x["pr_details"]))
    
#     # Define edges
#     workflow.add_edge("setup_context", "get_pr_details")
#     workflow.add_edge("get_pr_details", "review_code")
    
#     return workflow

# Example usage
# if __name__ == "__main__":
#     # Initialize agent
#     # Github(github_token)
#     client = Github("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")
#     repo_url = "https://github.com/krish-patel1003/RMS"
#     agent = CodeReviewAgent(repo_url=repo_url, github_service=client)
#     agent.setup_repo_context(repo_url=repo_url)

    
    # # Create workflow
    # workflow = create_review_workflow()
    
    # # Run review
    # result = workflow.run({
    #     "agent": agent,
    #     "pr_branch": "feature-branch"
    # })
    
    # print(result["review_code"])
"""
Please review the following code:
[paste your code]
Consider:
1. Code quality and adherence to best practices
2. Potential bugs or edge cases
3. Performance optimizations
4. Readability and maintainability
5. Any security concerns
Suggest improvements and explain your reasoning for each suggestion.
"""

