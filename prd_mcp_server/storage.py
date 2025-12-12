"""
PRD Storage Module
Handles PRD storage in GCS and search via Vertex AI Search (Discovery Engine)
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.cloud import storage
from google.cloud import discoveryengine_v1 as discoveryengine
import markdown


def markdown_to_html(md_content: str) -> str:
    """
    Convert markdown content to HTML.
    Returns a complete HTML document with basic styling.
    """
    md = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
    html_body = md.convert(md_content)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PRD</title>
    <style>
        body {{
            font-family: sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""


class PRDStorage:
    def __init__(
        self,
        bucket_name: str,
        datastore_id: str,
        project_id: str,
        location: str = "global"
    ):
        self.bucket_name = bucket_name
        self.datastore_id = datastore_id
        self.project_id = project_id
        self.location = location

        # Initialize GCS client
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.bucket(bucket_name)

        # Initialize Discovery Engine client for search
        self.search_client = discoveryengine.SearchServiceClient()

        # Build serving config name for search
        # Note: Using engine ID format for Vertex AI Search
        self.serving_config = (
            f"projects/{project_id}/locations/{location}/"
            f"collections/default_collection/engines/{datastore_id}/"
            f"servingConfigs/default_search"
        )

    def store_prd(
        self,
        product_name: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Store a PRD to GCS bucket in both markdown and HTML formats.
        Returns the PRD ID and storage locations.
        """
        # Generate timestamp and PRD ID
        timestamp = datetime.utcnow().isoformat()
        prd_id = f"{product_name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

        # Prepare metadata
        prd_metadata = metadata or {}
        prd_metadata.update({
            "product_name": product_name,
            "created_at": timestamp,
            "prd_id": prd_id
        })

        # Extract summary from PRD content (first 200 chars of Problem Statement)
        summary = self._extract_summary(content)
        prd_metadata["summary"] = summary

        # Store MARKDOWN version (for users)
        md_blob_path = f"prds/{prd_id}.md"
        md_blob = self.bucket.blob(md_blob_path)
        md_blob.metadata = prd_metadata
        md_blob.upload_from_string(content, content_type="text/plain")

        # Convert and store HTML version (for Vertex AI Search)
        html_content = markdown_to_html(content)
        html_blob_path = f"prds/{prd_id}.html"
        html_blob = self.bucket.blob(html_blob_path)
        html_blob.metadata = prd_metadata
        html_blob.upload_from_string(html_content, content_type="text/html")

        # Get public URL for HTML file (no authentication needed with uniform bucket-level access)
        html_public_url = f"https://storage.googleapis.com/{self.bucket_name}/{html_blob_path}"

        return {
            "prd_id": prd_id,
            "gcs_path_markdown": f"gs://{self.bucket_name}/{md_blob_path}",
            "gcs_path_html": f"gs://{self.bucket_name}/{html_blob_path}",
            "html_url": html_public_url,
            "product_name": product_name,
            "created_at": timestamp,
            "summary": summary
        }

    def get_prd(self, prd_id: str) -> Optional[Dict]:
        """
        Retrieve a PRD by ID from GCS.
        Returns PRD content and metadata, or None if not found.
        """
        blob_path = f"prds/{prd_id}.md"
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            return None

        # Download content
        content = blob.download_as_text()

        # Get metadata
        blob.reload()  # Refresh to get metadata
        metadata = blob.metadata or {}

        return {
            "prd_id": prd_id,
            "content": content,
            "product_name": metadata.get("product_name", "Unknown"),
            "created_at": metadata.get("created_at", ""),
            "summary": metadata.get("summary", ""),
            "gcs_path": f"gs://{self.bucket_name}/{blob_path}"
        }

    def search_prds(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search PRDs using Vertex AI Search (Discovery Engine).
        Returns list of matching PRDs with summaries.
        """
        # Build search request
        request = discoveryengine.SearchRequest(
            serving_config=self.serving_config,
            query=query,
            page_size=max_results,
            # Enable snippets for better context
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True
                ),
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=max_results
                )
            )
        )

        try:
            # Execute search
            response = self.search_client.search(request=request)

            results = []
            for result in response.results:
                document = result.document

                # Extract PRD ID from document name
                # Document name format: projects/.../locations/.../dataStores/.../branches/.../documents/{doc_id}
                doc_id = document.name.split("/")[-1]
                # Handle both .md and .html extensions
                prd_id = doc_id.replace(".html", "").replace(".md", "")

                # Get struct data (metadata)
                struct_data = document.struct_data

                # Extract snippet if available
                snippet = ""
                if result.document.derived_struct_data:
                    snippets = result.document.derived_struct_data.get("snippets", [])
                    if snippets:
                        snippet = snippets[0].get("snippet", "")

                results.append({
                    "prd_id": prd_id,
                    "product_name": struct_data.get("product_name", "Unknown"),
                    "summary": struct_data.get("summary", ""),
                    "snippet": snippet,
                    "created_at": struct_data.get("created_at", ""),
                    "relevance_score": getattr(result, "relevance_score", 0.0)
                })

            return results

        except Exception as e:
            # If search fails (e.g., data store not ready), fall back to simple GCS listing
            print(f"Search failed: {e}. Falling back to GCS listing.")
            return self._fallback_search(query, max_results)

    def _fallback_search(self, query: str, max_results: int) -> List[Dict]:
        """
        Fallback search using simple GCS listing and keyword matching.
        Used when Vertex AI Search is not available.
        """
        query_lower = query.lower()
        results = []

        # List all PRD blobs
        blobs = self.bucket.list_blobs(prefix="prds/")

        for blob in blobs:
            if not blob.name.endswith(".md"):
                continue

            # Get metadata
            blob.reload()
            metadata = blob.metadata or {}

            # Simple keyword matching
            product_name = metadata.get("product_name", "").lower()
            summary = metadata.get("summary", "").lower()

            if query_lower in product_name or query_lower in summary:
                prd_id = blob.name.replace("prds/", "").replace(".md", "")
                results.append({
                    "prd_id": prd_id,
                    "product_name": metadata.get("product_name", "Unknown"),
                    "summary": metadata.get("summary", ""),
                    "snippet": summary[:200] if summary else "",
                    "created_at": metadata.get("created_at", ""),
                    "relevance_score": 1.0  # No real scoring in fallback
                })

                if len(results) >= max_results:
                    break

        return results

    @staticmethod
    def _extract_summary(content: str, max_length: int = 200) -> str:
        """
        Extract summary from PRD content.
        Looks for Problem Statement section or uses first paragraph.
        """
        lines = content.split("\n")

        # Try to find Problem Statement section
        in_problem_section = False
        problem_text = []

        for line in lines:
            if "problem statement" in line.lower() or "## problem" in line.lower():
                in_problem_section = True
                continue

            if in_problem_section:
                if line.strip().startswith("#"):  # Next section
                    break
                if line.strip():
                    problem_text.append(line.strip())

        if problem_text:
            summary = " ".join(problem_text)
        else:
            # Fallback: use first non-empty, non-header lines
            summary = " ".join([
                line.strip() for line in lines
                if line.strip() and not line.strip().startswith("#")
            ][:3])

        # Truncate to max length
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary or "No summary available"
