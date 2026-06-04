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

You will receive a list of files. Group them logically by Project, Subject, or Client based on filenames and metadata.
RULES:
1. NEVER create a folder with a generic name like "Documents" or "Misc". Use highly specific names (e.g., "Q3 Financial Reports", "React Frontend Assets").
2. DO NOT hallucinate files. Only route the exact file IDs provided in the input.
3. Maximum folder depth is 2 levels (e.g., "University/Calculus").
4. Your output MUST be a JSON object with this exact structure:

{{
  "summary": "One sentence summary of what was organized",
  "groups": [
    {{
      "folder_name": "Highly Specific Name",
      "reason": "Short reason why these files were grouped",
      "confidence": 0.95,
      "file_ids": [1, 2, 3]
    }}
  ]
}}

Here are the files to organize:
{files_data}
"""

def _chunk_files(files: List[FileObject], chunk_size: int = 100) -> List[List[FileObject]]:
    """Split files into smaller batches to prevent LLM context overflow."""
    return [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]

def format_files_for_prompt(files: List[FileObject]) -> str:
    """Format files into a compact JSON string to save tokens (using IDs)."""
    minimal_files = []
    for f in files:
        minimal_files.append({
            "id": f.id,
            "name": f.name,
            "ext": f.ext,
            "size": f.size
        })
    return json.dumps(minimal_files, indent=2)

def ai_organize_batch(files: List[FileObject], retries: int = 3) -> OrganizationPlan:
    """
    Sends a batch of files to Ollama and returns a validated Pydantic object.
    Includes auto-retry for JSON validation failures.
    """
    files_data = format_files_for_prompt(files)
    prompt = PROMPT_TEMPLATE.format(
        files_data=files_data
    )
    
    model_name = ollama_manager.get_active_model()
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
            # On retry, we could append the error to the prompt, but for now we just try again
            payload["prompt"] = prompt + f"\n\nERROR ON LAST ATTEMPT:\n{e}\nFIX THE JSON AND TRY AGAIN."
            print(f"Validation failed (Attempt {attempt+1}/{retries}): {e}")
        except Exception as e:
            last_error = str(e)
            print(f"Request failed: {e}")
            break
            
    # Fallback if all retries fail
    print(f"AI failed to organize batch. Last error: {last_error}")
    # Return a safe fallback putting them in a "Requires Manual Sorting" folder
    return OrganizationPlan(
        summary="AI generation failed. Fallback applied.",
        groups=[{
            "folder_name": "Requires Manual Sorting",
            "reason": f"AI Error: {last_error}",
            "confidence": 0.0,
            "file_ids": [f.id for f in files]
        }]
    )
