#!/usr/bin/env python
import json
import os
from typing import List, Dict, Any

from pydantic import BaseModel

from crewai.flow import Flow, listen, start
from crewai import Crew, Process

from anki_flow.crews.anki_crew.crew import AnkiCrew


class AnkiState(BaseModel):
    deck_name: str | None = None
    flashcards: List[Dict[str, Any]] | None = None
    approved: bool = False


def _abs_notes_folder() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, "notes_folder")


def _save_flashcards_to_file(flashcards: List[Dict[str, Any]], path: str = None) -> None:
    # Default path: save to anki_flow/flashcards directory
    if path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        flashcards_dir = os.path.join(base_dir, "flashcards")
        os.makedirs(flashcards_dir, exist_ok=True)
        path = os.path.join(flashcards_dir, "flashcards.json")
    
    # Save under a top-level dictionary key "flashcards"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"flashcards": flashcards}, f, ensure_ascii=False, indent=2)


def _run_generate_flashcards(deck_name: str) -> List[Dict[str, Any]]:
    inputs = {
        "folder_path": _abs_notes_folder(),
        "deck_name": deck_name,
        # Optional inputs used by prompts; safe defaults
        "model_name": os.environ.get("ANKI_MODEL", "Basic"),
        "tags": os.environ.get("ANKI_TAGS", "").split(",") if os.environ.get("ANKI_TAGS") else [],
    }

    # Build a crew that contains only the generation task
    crew_builder = AnkiCrew()
    generator_agent = crew_builder.flashcard_generator()
    generate_task = crew_builder.generate_flashcards()
    generation_crew = Crew(
        agents=[generator_agent],
        tasks=[generate_task],
        process=Process.sequential,
        verbose=True,
    )

    result = generation_crew.kickoff(inputs=inputs)

    raw = getattr(result, "raw", result)
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="ignore")

    # Parse result into a JSON array of flashcards
    try:
        data = json.loads(raw)
    except Exception as exc:
        # Attempt to extract JSON array substring as fallback
        start_idx = str(raw).find("[")
        end_idx = str(raw).rfind("]")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            data = json.loads(str(raw)[start_idx : end_idx + 1])
        else:
            raise ValueError("Failed to parse generated flashcards JSON.") from exc

    if not isinstance(data, list):
        raise ValueError("Generated output is not a JSON array of flashcards.")

    return data


def _upload_to_anki(deck_name: str, notes: List[Dict[str, Any]]) -> Dict[str, Any]:
    inputs = {
        "deck_name": deck_name,
        "model_name": os.environ.get("ANKI_MODEL", "Basic"),
        "tags": os.environ.get("ANKI_TAGS", "").split(",") if os.environ.get("ANKI_TAGS") else [],
        "flashcards": notes,
    }

    crew_builder = AnkiCrew()
    uploader_agent = crew_builder.anki_uploader()
    upload_task = crew_builder.upload_to_anki()
    upload_crew = Crew(
        agents=[uploader_agent],
        tasks=[upload_task],
        process=Process.sequential,
        verbose=True,
    )

    result = upload_crew.kickoff(inputs=inputs)
    raw = getattr(result, "raw", result)
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="ignore")
    try:
        return json.loads(raw)
    except Exception:
        return {"error": f"Unexpected upload response: {raw}"}


def upload_only():
    """
    Upload previously generated flashcards without regenerating.
    Reads from flashcards.json and asks for deck name.
    """
    import time
    import os
    
    # Clear screen for clean interface
    time.sleep(0.2)
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("========================")
    print("ANKI UPLOAD ONLY")
    print("========================")
    deck_name = input("Enter deck name: ")
    print(f"✓ Deck name set to: {deck_name}")
    print("========================")
    
    try:
        # Read from anki_flow/flashcards directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        flashcards_path = os.path.join(base_dir, "flashcards", "flashcards.json")
        with open(flashcards_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        notes = data.get("flashcards")
        if not isinstance(notes, list):
            raise ValueError("Invalid flashcards.json format: 'flashcards' must be a list.")
    except FileNotFoundError:
        print("flashcards.json not found in anki_flow/flashcards directory. Generate flashcards first.")
        return
    except Exception as exc:
        print(f"Failed to read flashcards.json: {exc}")
        return

    result = _upload_to_anki(deck_name, notes)
    if result.get("error"):
        print(f"Upload failed: {result['error']}")
    else:
        print("Upload completed.")


class AnkiFlow(Flow[AnkiState]):
    def __init__(self):
        super().__init__()
        while True:
            name_of_deck = input("Enter name of deck: ")
            if name_of_deck:
                break
            else:
                print("Please type a name for the deck.")
        self.name_of_deck = name_of_deck

    @start()
    def deck_name_input(self):
        self.state.deck_name = self.name_of_deck
        print(f"✓ Deck name set to: {self.state.deck_name}")
     
    @listen(deck_name_input)
    def generate_and_review(self):
        while True:
            print("Generating flashcards from notes...")
            flashcards = _run_generate_flashcards(self.state.deck_name)
            self.state.flashcards = flashcards
            _save_flashcards_to_file(flashcards)
            print("Flashcards saved to 'anki_flow/flashcards/flashcards.json'.")

            while True:
                answer = input("Check flashcards. Do you approve them? (y/n) ").strip().lower()
                if answer == "y":
                    # Mark as approved; a dedicated step will handle upload
                    self.state.approved = True
                    return  # Exit both loops
                elif answer == "n":
                    print("Regenerating flashcards...")
                    break  # Break inner loop to regenerate
                else:
                    print("Wrong answer. Type either 'y' to accept or 'n' to generate a new set of flashcards.")
                    # Continue inner loop to ask again



    @listen(generate_and_review)
    def send_to_anki(self):
        if not self.state.approved:
            return
        if not self.state.flashcards or len(self.state.flashcards) == 0:
            print("No flashcards to upload. Please add notes to the notes_folder and try again.")
            return
        print("Uploading flashcards to Anki...")
        upload_result = _upload_to_anki(self.state.deck_name, self.state.flashcards)
        if upload_result.get("error"):
            print(f"Upload failed: {upload_result['error']}")
        else:
            print("Upload completed.")


def kickoff():
    anki_flow = AnkiFlow()
    anki_flow.kickoff()


def plot():
    anki_flow = AnkiFlow()
    anki_flow.plot()


if __name__ == "__main__":
    kickoff()
