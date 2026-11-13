# Music AI Agent

## Overview

Music AI Agent is a Python command-line application that helps music creators organize their unreleased songs and decide what to work on next.

I built it to solve a problem I faced while making music: I had a growing collection of unfinished songs, but no clear way to track their progress or prioritize them. The application brings song ratings, genres, notes, completion percentages, and tasks into one place.

An AI assistant powered by OpenAI GPT-4o uses that saved information to answer questions, suggest priorities, and turn notes into actionable tasks. For example, a note such as *"The hook is super catchy"* is useful feedback, but doesn't necessarily need to become a task. A note such as *"Re-record the chorus vocals"* suggests a specific action.

**The AI works with song metadata and written notes; it does not listen to or analyze the audio itself.**

## Features

- **Song library:** Scan a local folder for MP3 and WAV files and maintain a JSON database of song information.
- **Ratings and genres:** Rate songs during initial setup and assign one or more genres. Genres can also be updated through the agent.
- **Progress tracking:** Track eight production areas—beat, lyrics, hook, verse 1, verse 2, vocals, adlibs, and final mix—with an overall completion score.
- **Audio playback:** Open songs from the application using the default audio player on Windows.
- **AI-powered guidance:** Ask which songs to prioritize and which production areas still need work, based on saved ratings, progress, and notes.
- **Natural-language song management:** Retrieve song information, update progress and genres, rename song files, and add or remove notes.
- **Task management:** Add, edit, complete, reopen, and remove tasks for individual songs.
- **Task generation:** Ask the AI to suggest actionable tasks from your existing song notes.
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
3. **Accept a request:** You type a question or instruction into the terminal.
4. **Select tools:** GPT-4o receives the conversation and available tool definitions, then chooses whether to call a Python function.
5. **Execute tools:** The application checks song-name matches, executes the selected function, and returns its result to the model.
6. **Respond and save:** The agent replies in natural language, and database changes are saved to JSON.

Tool definitions are generated from Python function signatures, type annotations, and docstrings using a custom `@register_tool` decorator in `tool_registry.py`.

## Installation and Setup

### Prerequisites

- **Windows** (audio playback currently uses `os.startfile`)
- **Python 3.12 or newer**
- An **OpenAI API key** with API access (API usage may incur charges)
- A local folder containing MP3 or WAV files

### 1. Clone the repository

Replace the example repository URL with the actual GitHub URL:

```bash
git clone https://github.com/YOUR-USERNAME/Music-AI-Agent.git
cd Music-AI-Agent
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

Replace both placeholders with your own values. `SONGS_PATH` must point to an existing folder. Forward slashes work for Windows paths in this example.

**Do not commit your `.env` file or your personal song database to GitHub.**

### 4. Run the application

```bash
python main.py
```

On first run, the application scans your music folder and may ask you to rate songs and enter missing metadata before starting the AI chat.

## Example Requests

```text
Which of my highest-rated songs should I finish first?
Show me the completion progress for my song Designer.
What should I work on next for Designer?
Generate tasks for Designer based on its notes.
Mark task 2 for Designer as completed.
Add a note to Designer: Try a different hook melody.
```

Song names and task numbers above are illustrative; use names and numbers from your own database.

## Project Files

| File | Purpose |
| --- | --- |
| `main.py` | Song management, local JSON persistence, AI tools, and terminal chat |
| `tool_registry.py` | Decorator-based tool registration and JSON schema generation |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for required environment variables |
| `all_songs.example.json` | Sample song metadata structure (not automatically loaded) |
| `.gitignore` | Excludes local credentials, personal song data, audio files, and generated files |

## Current Limitations

- The application uses a **terminal interface**, not a graphical interface.
- Audio playback currently depends on **Windows**.
- AI recommendations are based on **saved metadata and notes**, not direct audio analysis.
- Ratings are collected during song setup; the AI tools do not currently provide a separate rating-update action.

## Why I Built It

This project combines a practical music workflow with Python, JSON persistence, API integration, automatic tool-schema generation, and LLM function calling. Its goal is to make it easier to move from a large collection of unfinished ideas to a clear next action.