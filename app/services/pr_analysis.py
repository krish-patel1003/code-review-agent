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
import requests
from app.services.github_integration import PRDetails

@dataclass
class RepoContext:
    repo_url: str
    files: List[str]
    tree_structure: str
    file_contents: List[Dict]


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


    def review_changes(self, pr_details: PRDetails) -> str:
        """Review code changes using the LLM"""
        review_template = """
            You are an expert code reviewer. Please review the following code changes:

                Context:
                Files changed: {files_changed}

                Changes:
                {diff_content}

                Consider:
                1. Code quality and adherence to best practices
                2. Potential bugs or edge cases
                3. Performance optimizations
                4. Readability and maintainability
                5. Any security concerns

                Provide a detailed review with specific suggestions for improvements. Format your response as:
                - Summary of changes
                - Key concerns (if any)
                - Specific recommendations
                - Positive aspects
        """
        
        prompt = ChatPromptTemplate.from_template(review_template)
        
        # Get relevant context from vector store
        relevant_docs = []
        for file in pr_details.files:
            results = self.vector_store.similarity_search(
                file.filename,
                k=2,
                filter={"type": "content"}
            )
            relevant_docs.extend(results)
        
        # Combine diff content
        diff_text = "\n".join([
            f"=== {file.filename} ===\n{file.content}\n"
            for file in pr_details.files
        ])
        
        # Generate review
        review = self.llm.predict(
            prompt.format(
                files_changed=", ".join([file.filename for file in pr_details.files]),
                diff_content=diff_text
            )
        )
        
        return review

