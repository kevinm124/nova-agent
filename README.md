# 🤖 Nova: Personal AI Agent

A personal assistant that runs on your computer and understands plain language. Ask it how your PC is doing, tell it to tidy up your Downloads, find a file or open an app, and it picks the right tool and does it.

Built with Python and Google Gemini using **tool calling**: the AI decides which function to run, the program runs it, and the AI explains the result.

## What it can do

| Ask | What happens |
|---|---|
| *"How is my computer doing?"* | Checks CPU, RAM, disks, battery and the most memory-hungry apps |
| *"Clean up my Downloads"* | Sorts files into Images, Documents, Videos, Archives… |
| *"Find my CV"* | Searches your files by name |
| *"Open VS Code"* | Launches an app from an allow-list |
| *"Remember I have an exam on Friday"* | Saves notes you can list or delete later |

Works in English and Slovenian.

## Safety

- Anything that moves or deletes asks for confirmation first.
- Files are never overwritten. Duplicates get renamed.
- Apps can only be opened from a fixed allow-list, so the AI can't run arbitrary commands.

## Setup

1. Get a free API key at [Google AI Studio](https://aistudio.google.com/apikey).
2. Create a virtual environment so the packages stay inside the project folder:

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
```

3. Install and configure:

```bash
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

4. Paste your key into `.env`, then run:

```bash
python main.py
```

Next time, just activate the environment (step 2, second line) and run `python main.py`.

## Uninstall

If you used the virtual environment, delete the `.venv` folder and everything is gone.

If you installed without one:

```bash
pip uninstall -r requirements.txt -y
```

## How it's built

```
main.py    → terminal interface (input, output, confirmations)
agent.py   → talks to Gemini and hands it the tools
tools.py   → the actual actions: system status, files, apps, notes
```

The agent doesn't depend on the interface, so a graphical UI can be added without touching the tools.

## Adding a tool

Write a Python function with a clear docstring in `tools.py` and add it to `ALL_TOOLS`. Gemini reads the docstring to know when to use it.

## Roadmap

- [ ] Graphical interface
- [ ] Voice commands
- [ ] Reminders with notifications