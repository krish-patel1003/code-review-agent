from typing import Dict, List
from dataclasses import dataclass
from app.services import GithubService
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_chroma import Chroma
from app.services.github_integration import PRDetails
import json

@dataclass
class RepoContext:
    repo_url: str
    files: List[str]
    tree_structure: str
    file_contents: List[Dict]


class CodeReviewAgent:
    def __init__(
        self,
        github_service: GithubService,
        api_key: str,
        chat_model: str,
        embedding_model: str,
    ):
        self.github_client = github_service
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=chat_model,
                google_api_key=api_key,
                temperature=0.3,
                top_k=40,
                top_p=0.95,
                max_output_tokens=4096,
                response_mime_type="application/json",
            )

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=embedding_model,
                google_api_key=api_key,
                task_type="retrieval_document",
            )

        except Exception as e:
            raise Exception(f"Failed to initialize Gemini API: {e}")

        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

    @staticmethod
    def _coerce_llm_text(review) -> str:
        if hasattr(review, "content"):
            content = review.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        parts.append(block["text"])
                    elif isinstance(block, str):
                        parts.append(block)
                if parts:
                    return "\n".join(parts)
            return str(content)
        return str(review)

    def setup_repo_context(self, repo_url: str) -> RepoContext:
        tree_structure, file_paths = self.github_client.get_tree_strucutre_and_file_paths(repo_url)
        default_branch = self.github_client.get_default_branch(repo_url)
        texts = []
        metadatas = []
        file_contents = []

        for file_path in file_paths:
            file_content = self.github_client.get_file_content(repo_url, file_path, ref=default_branch)
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
        file_review_template = """
You are an expert code reviewer analyzing ONE changed file.

Repository structure:
{repo_structure}

Related repository context:
{relevant_context}

Changed file: {filename}
File status: {file_status}
Additions: {file_additions}
Deletions: {file_deletions}

PR patch for this file:
{file_patch}

Current file content at PR head:
{file_content}

Find as many real issues as possible in this file's changed behavior. Do not stop at the first issue.
Focus on correctness bugs, edge cases, logic errors, unsafe behavior, and maintainability concerns.

Return ONLY valid JSON (no prose, no markdown) with this shape:
{{
  "files": [
    {{
      "filename": "string",
      "issue_type": "string",
      "line_number_of_issue": 0,
      "issue_description": "string",
      "suggestions": "string"
    }}
  ],
  "summary": {{
    "total_files_changed": 1,
    "total_issues": 0,
    "critical_issues": 0
  }}
}}
        """

        prompt = ChatPromptTemplate.from_template(file_review_template)

        if self.vector_store is None:
            raise RuntimeError("Repository context is not initialized")
        vector_store = self.vector_store

        all_issues = []
        critical_issues = 0

        for file in pr_details.files:
            results = vector_store.similarity_search(file.filename, k=6, filter={"type": "content"})
            relevant_context = "\n".join([doc.page_content for doc in results])

            final_prompt = prompt.invoke({
                "repo_structure": repo_context.tree_structure,
                "relevant_context": relevant_context,
                "filename": file.filename,
                "file_status": file.status,
                "file_additions": file.additions,
                "file_deletions": file.deletions,
                "file_patch": file.patch or "(no patch available)",
                "file_content": file.content or "(file content unavailable)",
            })

            review = self.llm.invoke(final_prompt)
            parsed = self.parse_or_repair_review_response(self._coerce_llm_text(review))
            file_issues = parsed.get("files", []) if isinstance(parsed, dict) else []

            for issue in file_issues:
                if not isinstance(issue, dict):
                    continue
                if not issue.get("filename"):
                    issue["filename"] = file.filename
                issue_type = str(issue.get("issue_type", "")).lower()
                if "critical" in issue_type or "security" in issue_type:
                    critical_issues += 1
                all_issues.append(issue)

        deduped = []
        seen = set()
        for issue in all_issues:
            key = (
                str(issue.get("filename", "")),
                str(issue.get("line_number_of_issue", "")),
                str(issue.get("issue_description", "")).strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(issue)

        aggregate = {
            "files": deduped,
            "summary": {
                "total_files_changed": len(pr_details.files),
                "total_issues": len(deduped),
                "critical_issues": critical_issues,
            },
        }
        return json.dumps(aggregate)

    @staticmethod
    def _extract_json_object(raw: str) -> str:
        start = raw.find("{")
        if start == -1:
            return raw
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(raw)):
            char = raw[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return raw[start : index + 1]
        return raw[start:]

    @staticmethod
    def parse_review_response(review: str) -> Dict:
        text = review.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text

        text = text.strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

        candidate = CodeReviewAgent._extract_json_object(text)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = {
                "files": [],
                "summary": {
                    "total_files_changed": 0,
                    "total_issues": 0,
                    "critical_issues": 0,
                },
                "parse_error": "Model response was not valid JSON",
                "raw_response": text,
            }

        if not isinstance(parsed, dict):
            return {
                "files": [],
                "summary": {
                    "total_files_changed": 0,
                    "total_issues": 0,
                    "critical_issues": 0,
                },
                "parse_error": "Parsed review response is not a JSON object",
                "raw_response": str(parsed),
            }

        return parsed

    def parse_or_repair_review_response(self, review: str) -> Dict:
        parsed = self.parse_review_response(review)
        if "parse_error" not in parsed:
            return parsed

        repair_prompt = (
            "You are given malformed or partial JSON from a code review system.\n"
            "Return ONLY valid JSON with this exact shape:\n"
            "{\n"
            '  "files": [\n'
            "    {\n"
            '      "filename": "string",\n'
            '      "issue_type": "string",\n'
            '      "line_number_of_issue": 0,\n'
            '      "issue_description": "string",\n'
            '      "suggestions": "string"\n'
            "    }\n"
            "  ],\n"
            '  "summary": {\n'
            '    "total_files_changed": 0,\n'
            '    "total_issues": 0,\n'
            '    "critical_issues": 0\n'
            "  }\n"
            "}\n\n"
            "Rules:\n"
            "- Preserve only issues clearly present in input.\n"
            "- If uncertain, omit issue entries.\n"
            "- Ensure output is strict JSON.\n\n"
            f"Input:\n{review}"
        )

        repaired_review = self.llm.invoke(repair_prompt)
        repaired_text = repaired_review
        if hasattr(repaired_review, "content"):
            repaired_text = repaired_review.content
            if isinstance(repaired_text, list):
                parts = []
                for block in repaired_text:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        parts.append(block["text"])
                    elif isinstance(block, str):
                        parts.append(block)
                repaired_text = "\n".join(parts)
        repaired_parsed = self.parse_review_response(str(repaired_text))
        if "parse_error" in repaired_parsed:
            return parsed
        return repaired_parsed
