from crewai.tools import BaseTool
from typing import List, Optional, Tuple, Type
from pydantic import BaseModel, Field
import os
import json
from pathlib import Path
import requests


class ReadMarkdownFolderInput(BaseModel):
    """Schema for reading Markdown files from a folder."""
    folder_path: str = Field(..., description="Absolute path to folder with .md files.")
    recursive: bool = Field(default=True, description="Search subfolders for .md files as well.")

class ReadMarkdownFolderTool(BaseTool):
    name: str = "read_markdown_folder"
    description: str = (
        "Reads all .md files in a folder and returns a JSON list of objects with 'path' and 'content'. "
        "Use this to load study material before generating flashcards."
    )
    args_schema: Type[BaseModel] = ReadMarkdownFolderInput

    def _run(self, folder_path: str, recursive: bool = True) -> str:
        try:
            if not os.path.isabs(folder_path):
                return json.dumps({"error": "folder_path must be an absolute path"})
            if not os.path.isdir(folder_path):
                return json.dumps({"error": f"folder_path does not exist or is not a directory: {folder_path}"})
            md_files: List[Path] = []
            base = Path(folder_path)
            if recursive:
                md_files = list(base.rglob("*.md"))
            else:
                md_files = list(base.glob("*.md"))

            results: List[dict] = []
            for file_path in md_files:
                try:
                    text = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # Fallback encoding if necessary
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                results.append({"path": str(file_path), "content": text})

            return json.dumps(results)
        except OSError as e:
            return json.dumps({"error": str(e)})


class AnkiConnectAddNotesInput(BaseModel):
    """Schema to add notes to Anki via AnkiConnect."""
    deck_name: str = Field(..., description="Target Anki deck name. Will be created if missing.")
    model_name: str = Field(default="Basic", description="Anki note type/model to use, default 'Basic'.")
    notes: List[dict] = Field(
        ..., description=(
            "List of note dicts with at least fields: 'Front', 'Back'. "
            "Optional 'tags' (list[str])."
        )
    )
    anki_connect_url: str = Field(default="http://127.0.0.1:8765", description="AnkiConnect URL.")


class AnkiConnectAddNotesTool(BaseTool):
    name: str = "anki_connect_add_notes"
    description: str = (
        "Adds notes to Anki via AnkiConnect. Accepts deck, model, and notes with Front/Back."
    )
    args_schema: Type[BaseModel] = AnkiConnectAddNotesInput

    def _request(self, url: str, action: str, params: dict) -> Tuple[Optional[dict], Optional[str]]:
        try:
            response = requests.post(url, json={"action": action, "version": 6, "params": params}, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                return None, str(data["error"])
            return data.get("result"), None
        except requests.exceptions.ConnectionError as e:
            return None, f"Failed to connect to AnkiConnect at {url}. Make sure Anki is running with AnkiConnect add-on enabled. Original error: {str(e)}"
        except requests.exceptions.Timeout as e:
            return None, f"Timeout connecting to AnkiConnect at {url}. Anki might be slow to respond. Original error: {str(e)}"
        except requests.RequestException as e:
            return None, f"Request failed: {str(e)}"

    def _ensure_deck(self, url: str, deck_name: str) -> Optional[str]:
        _, err = self._request(url, "createDeck", {"deck": deck_name})
        return err

    def _ensure_model_fields(self, url: str, model_name: str) -> Tuple[bool, Optional[str]]:
        result, err = self._request(url, "modelFieldNames", {"modelName": model_name})
        if err:
            return False, err
        if not result or not isinstance(result, list):
            return False, "Invalid response for model field names"
        needed = {"Front", "Back"}
        if not needed.issubset(set(result)):
            return False, f"Model '{model_name}' missing required fields {needed}"
        return True, None

    def _run(self, deck_name: str, model_name: str = "Basic", notes: Optional[List[dict]] = None, anki_connect_url: str = "http://127.0.0.1:8765") -> str:
        try:
            if notes is None:
                notes = []
            # basic validation
            invalid_indices: List[int] = []
            for idx, n in enumerate(notes):
                fields = n.get("fields") or {"Front": n.get("Front"), "Back": n.get("Back")}
                if not fields or "Front" not in fields or "Back" not in fields:
                    invalid_indices.append(idx)
            if invalid_indices:
                return json.dumps({"error": f"Invalid notes at indices: {invalid_indices}. Each needs Front and Back."})
            if not deck_name.strip():
                return json.dumps({"error": "deck_name is required"})

            # Ensure deck exists
            err = self._ensure_deck(anki_connect_url, deck_name)
            if err:
                return json.dumps({"error": f"Failed to ensure deck: {err}"})

            ok, err = self._ensure_model_fields(anki_connect_url, model_name)
            if not ok:
                return json.dumps({"error": err})

            prepared_notes: List[dict] = []
            for n in notes:
                fields = n.get("fields") or {"Front": n.get("Front", ""), "Back": n.get("Back", "")}
                tags = n.get("tags", [])
                prepared_notes.append(
                    {
                        "deckName": deck_name,
                        "modelName": model_name,
                        "fields": fields,
                        "options": {"allowDuplicate": False},
                        "tags": tags,
                    }
                )

            result, err = self._request(anki_connect_url, "addNotes", {"notes": prepared_notes})
            if err:
                return json.dumps({"error": err})

            return json.dumps({"result": result})
        except requests.RequestException as e:
            return json.dumps({"error": str(e)})
