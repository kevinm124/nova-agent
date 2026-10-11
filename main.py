"""
Terminal interface for Nova. Run:  python main.py
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm

import tools
from agent import AGENT_NAME, Agent, MissingApiKey

console = Console()
status = None  # the "thinking..." spinner, so we can pause it for questions


def confirm_in_terminal(question: str) -> bool:
    status.stop()  # pause the spinner so the question is readable
    answer = Confirm.ask(f"[yellow]⚠  {question}[/yellow]")
    status.start()
    return answer


def show_tool(name: str):
    console.print(f"  [dim]⚙ {name}...[/dim]")


HELP = """[bold]Try asking:[/bold]
  • How is my computer doing?
  • Pospravi mi mapo Prenosi
  • Find my CV
  • Open VS Code
  • Remember that I have an exam on Friday

[bold]Commands:[/bold]  /new  start a new conversation   /help  this list   /exit  quit"""


def main():
    global status
    tools.confirm = confirm_in_terminal
    tools.on_tool_used = show_tool

    try:
        agent = Agent()
    except MissingApiKey as e:
        console.print(f"[red]{e}[/red]")
        return

    console.print(Panel(f"[bold cyan]{AGENT_NAME}[/bold cyan] is online.\n\n{HELP}", border_style="cyan"))

    while True:
        try:
            message = console.input("\n[bold green]You ›[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not message:
            continue
        if message == "/exit":
            break
        if message == "/help":
            console.print(HELP)
            continue
        if message == "/new":
            agent.new_conversation()
            console.print("[dim]Started a new conversation.[/dim]")
            continue

        status = console.status(f"[cyan]{AGENT_NAME} is thinking...[/cyan]")
        status.start()
        try:
            answer = agent.ask(message)
        except Exception as e:  # network problems, invalid key, rate limits...
            answer = f"Something went wrong: {e}"
        finally:
            status.stop()

        console.print(f"\n[bold cyan]{AGENT_NAME} ›[/bold cyan]")
        console.print(Markdown(answer))

    console.print(f"\n[cyan]{AGENT_NAME} signing off. 👋[/cyan]")


if __name__ == "__main__":
    main()
