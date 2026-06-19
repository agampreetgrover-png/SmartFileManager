import json
import requests
from typing import List
from pydantic import ValidationError
from core.models import FileObject, OrganizationPlan
from core import ollama_manager

OLLAMA_URL = "http://localhost:11434/api/generate"

# Pydantic will auto-generate the JSON schema we need the LLM to follow
PLAN_SCHEMA = OrganizationPlan.model_json_schema()

PROMPT_TEMPLATE = """You are a deterministic file sorting system. Your ONLY output must be valid JSON.

You will receive a list of files. Group them logically by Project, Subject, Client, Event, or Workstream based on filenames and metadata.
RULES:
1. NEVER create a folder with a generic name like "Documents", "Misc", "Other", or "Temp".
2. Use highly specific, meaningful names (e.g. "Q4 Tax Invoices", "Marketing Photos 2025", "React App Components").
3. If a file is clearly part of a known project, client, or event, group it together.
4. Only route the exact file IDs provided in the input. Do not add, remove, or invent file IDs.
5. Use at most 2 levels of folder depth (for example "Client/Proposal" or "2024/Receipts").
6. Keep groups concise and avoid duplicates. Each file ID must appear in exactly one group.
7. If some files do not clearly belong to a specific project, group them into a useful descriptive folder such as "Invoices", "Photos", "Meeting Notes", or "Code Snippets" rather than a generic container.
8. List all files, even if a few are grouped into broad helpful categories.
9. Treat this request as a fresh scan: do not assume prior classifications, and do not reuse previous results unless the AI request fails.

Output structure MUST be exactly this JSON:
{
  "summary": "One sentence summary of what was organized",
  "groups": [
    {
      "folder_name": "Highly Specific Name",
      "reason": "Short reason why these files were grouped",
      "confidence": 0.95,
      "file_ids": [1, 2, 3]
    }
  ]
}

Example:
{
  "summary": "Organized 27 files into focused project and content buckets.",
  "groups": [
    {
      "folder_name": "2025 Tax Receipts",
      "reason": "Receipts and invoices for the 2025 tax year",
      "confidence": 0.96,
      "file_ids": [2, 5, 8]
    },
    {
      "folder_name": "ClientX Presentation",
      "reason": "Slides and notes for ClientX project deliverables",
      "confidence": 0.93,
      "file_ids": [3, 6]
    }
  ]
}

Here are the files to organize with metadata:
{files_data}
"""

def _chunk_files(files: List[FileObject], chunk_size: int = 100) -> List[List[FileObject]]:
    """Split files into smaller batches to prevent LLM context overflow."""
    return [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]

def format_files_for_prompt(files: List[FileObject]) -> str:
    """Format files into a compact JSON string for the LLM prompt."""
    minimal_files = []
    for f in files:
        minimal_files.append({
            "id": f.id,
            "name": f.name,
            "ext": f.ext,
            "size": f.size,
            "original_path": f.original_path
        })
    return json.dumps(minimal_files, indent=2, ensure_ascii=False)

def ai_organize_batch(files: List[FileObject], retries: int = 3) -> OrganizationPlan:
    """
    Sends a batch of files to Ollama and returns a validated Pydantic object.
    Includes auto-retry for JSON validation failures.
    """
    files_data = format_files_for_prompt(files)
    model_name = ollama_manager.get_active_model()

    prompt = PROMPT_TEMPLATE.replace("{files_data}", files_data)

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json"  # Forces Ollama to output JSON
    }

    last_error = None

    for attempt in range(retries):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=300)
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "")
            print(f"RAW LLM OUTPUT:\n{response_text}")

            # Pydantic strict validation
            plan = OrganizationPlan.model_validate_json(response_text)
            return plan

        except ValidationError as e:
            last_error = f"Pydantic Validation Error: {e}"
            payload["prompt"] = prompt + f"\n\nERROR ON LAST ATTEMPT:\n{e}\nFIX THE JSON AND TRY AGAIN."
            print(f"Validation failed (Attempt {attempt+1}/{retries}): {e}")
        except Exception as e:
            last_error = str(e)
            print(f"Request failed: {e}")
            break

    print(f"AI failed to organize batch. Last error: {last_error}")
    return OrganizationPlan(
        summary="AI generation failed. Fallback applied.",
        groups=[{
            "folder_name": "Requires Manual Sorting",
            "reason": f"AI Error: {last_error}",
            "confidence": 0.0,
            "file_ids": [f.id for f in files]
        }]
    )
