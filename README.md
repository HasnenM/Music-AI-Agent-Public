# Music AI Agent

## Overview

Music AI Agent is a Python command-line application that helps music creators organize their unreleased songs and decide what to work on next.

I built it to solve a problem I faced while making music: I had a growing collection of unfinished songs, but no clear way to track their progress or prioritize them. The application brings song ratings, genres, notes, completion percentages, and tasks into one place.

An AI assistant powered by OpenAI GPT-4o uses this information to answer questions, suggest priorities, and turn notes into actionable tasks.

For example, a note such as *"The hook is super catchy"* is useful feedback but doesn't necessarily need to become a task. A note such as *"Re-record the chorus vocals"* suggests a specific action.

**The AI works with song metadata and written notes; it does not listen to or analyze the audio itself.**

## Features

- **Song library:** Scan a local folder for MP3 and WAV files and maintain a JSON database of song information.
- **Ratings and genres:** Rate songs during initial setup and assign one or more genres. Genres can also be updated through the agent.
- **Progress tracking:** Track eight production areas—beat, lyrics, hook, verse 1, verse 2, vocals, adlibs, and final mix—with an overall completion score.
- **Audio playback:** Open songs using the default audio player on Windows.
- **AI-powered guidance:** Ask which songs to prioritize and which production areas still need work, based on saved ratings, progress, and notes.
- **Natural-language song management:** Retrieve song information, update progress and genres, rename song files, and add or remove notes.
- **Task management:** Add, edit, complete, reopen, and remove tasks for individual songs.
- **AI task generation:** Generate suggested tasks from existing song notes.
- **Persistent storage:** Save changes to `all_songs.json` so they remain available across sessions.

## Tech Stack

- **Language:** Python
- **LLM:** OpenAI GPT-4o
- **LLM integration:** LiteLLM (tool/function calling)
- **Data storage:** JSON
- **Environment variables:** python-dotenv
- **Development tools:** Visual Studio Code, Git, and GitHub

## How It Works

1. **Scan songs:** On startup, the application scans the folder specified by `SONGS_PATH` and loads or creates `all_songs.json`.
2. **Collect metadata:** For songs missing information, it prompts for ratings, genres, notes, and completion percentages.
3. **Accept a request:** The user enters a question or instruction in the terminal.
4. **Select tools:** GPT-4o receives the conversation and available tool definitions, then decides whether to call a Python function.
5. **Execute tools:** The application resolves song-name matches, executes the selected function, and returns the result to the model.
6. **Respond and save:** The agent responds in natural language, and changes to song data are saved to JSON.

Tool definitions are generated automatically from Python function signatures, type annotations, and docstrings using a custom `@register_tool` decorator in `tool_registry.py`.

## Technical Highlights

- **Dynamic tool registration:** Built a decorator-based registry that generates LLM tool schemas from Python functions, reducing repetitive tool definitions.
- **LLM function calling:** Implemented a tool execution workflow that connects natural-language requests to Python functions, processes results, and maintains conversation context.
- **Persistent data management:** Used JSON storage to maintain song metadata, notes, progress, and tasks across application sessions.
- **Input handling:** Added partial song-name matching, ambiguity handling, task-number validation, and error handling for invalid operations.

## Installation and Setup

### Prerequisites

- Windows (audio playback currently uses `os.startfile`)
- Python 3.14 (used during development; other versions have not been fully verified)
- An OpenAI API key with API access (usage may incur charges)
- A local folder containing MP3 or WAV files

### 1. Clone the repository

```bash
git clone https://github.com/HasnenM/Music-AI-Agent-Public.git
cd Music-AI-Agent-Public
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root, using `.env.example` as a template:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
SONGS_PATH=C:/Users/YourName/Music/Songs
```

Replace both placeholders with your own values. `SONGS_PATH` must point to an existing folder.

**Do not commit your `.env` file or personal song database to GitHub.**

### 4. Run the application

```bash
python main.py
```

On first run, the application scans your music folder and may ask you to enter missing song metadata before starting the AI chat.

## Example Requests

```text
Which of my highest-rated songs should I finish first?
Show me the completion progress for my song.
What should I work on next for this song?
Generate tasks based on its notes.
Mark task 2 as completed.
Add a note: Try a different hook melody.
```

These are illustrative examples. Use song names and task numbers from your own database when interacting with the agent.

## Project Files

| File | Purpose |
| --- | --- |
| `main.py` | Song management, JSON persistence, AI tools, and terminal chat |
| `tool_registry.py` | Decorator-based tool registration and JSON schema generation |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for required environment variables |
| `all_songs.example.json` | Example song metadata structure (not automatically loaded) |
| `.gitignore` | Excludes credentials, personal song data, audio files, and generated files |

## Current Limitations

- The application uses a terminal interface rather than a graphical interface.
- Audio playback currently depends on Windows.
- AI recommendations are based on saved metadata and notes, not direct audio analysis.
- AI-generated tasks may occasionally be repetitive or require manual review.
- Ratings are collected during song setup; the AI tools do not currently provide a separate rating-update action.