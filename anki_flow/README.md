# Anki Agent AI

Anki Agent AI creates study flashcards from your notes and sends them to Anki automatically.
It supports .pdf, .docx, .md, .txt, .csv, and .json files. Anki is a flashcard app available on desktop, web, and mobile.

## Disclaimer

If you encounter any problem with installation, do not hesitate to ask ChatGPT or Perplexity. It will resolve 99% of problems.

## What you need

- Python
- Anki Desktop
- The AnkiConnect add‑on
- An OpenAI API key
- Internet connection

## Setup

### 1) Create your project

- Create a folder for the agent (for example, "Anki Agent AI").
- Download a ZIP and unpack in that folder or clone a repo there.

### 2) Install Anki Desktop

- Download and install from https://apps.ankiweb.net/
- Create or sign in to your Anki account to sync.

#### Install the AnkiConnect add‑on

1. Open the Anki desktop app
2. Go to Tools → Add‑ons
3. Click "Get Add‑ons..."
4. Enter this code: `2055492159`
5. Click OK
6. Restart Anki (important)

### 3) Create your OpenAI API key

- Sign in to `https://platform.openai.com` → Organization → API Keys → Create new secret key.
- Save the key now; you won’t see it again after closing the dialog.
- Important: your account needs credit. Go to Billing → Add to credit balance (for example, $10). You can turn off auto‑recharge afterward to not charge automatically.

### 4) Install Python

- Download and install Python using terminal:

```bash
sudo apt update
sudo apt install python3
```

- Alternatively, go to https://www.python.org/downloads/. Download and install latest version.

### 5) Install pip

- Install `pip` through terminal:

```bash
sudo apt update
sudo apt install python3-pip
```

### 6) Install virtual environment

- Install virtual environment through terminal:

```bash
sudo apt install python3.12-venv
```

### 7) Install Python dependencies

On terminal, go to the folder where you put the project and the requirements.txt file is located. Install the required packages using command:

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 8) Create a .env file

In your project folder where you cloned or unpacked zip, go to the "anki_flow" folder and create a file named `.env` with:

```
MODEL=gpt-4.1
OPENAI_API_KEY=your_api_key_here
```

## Run the agent

1. Open Anki Desktop and leave it running.
2. Open a terminal and go to your project folder (the one that contains `anki_flow`). The command looks like this:
   ```
   cd path/to/your/project/anki-agent/anki_flow
   ```
3. To generate flashcards and send them to Anki:
   ```
   crewai run
   ```

If sending fails (for example, you forgot to open Anki), you can upload previously generated flashcards only:

```
uv run upload-only
```

## What to expect

1. The program asks for the name of the Anki deck.
2. It generates flashcards from your notes.
3. You review the flashcards (shown in the terminal). They are also saved to `anki_flow/flashcards/flashcards.json`.
4. Type `y` to accept and send them to Anki, or `n` to regenerate.
5. When accepted, the agent sends the flashcards to Anki and finishes.

## Fallback: upload previously generated flashcards

1. Open a terminal and go to `anki_flow`.
2. Run:
   ```
   uv run upload-only
   ```
3. Enter the deck name when asked. The saved flashcards will be sent to Anki.
