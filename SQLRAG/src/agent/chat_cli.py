
from __future__ import annotations
import typer
from rich.console import Console
from rich.markdown import Markdown
import dotenv

from .chat_sql import answer_question
from .validation import validate_env, validate_db_schema


app = typer.Typer(add_completion=False)
console = Console()


@app.callback()
def main():
    dotenv.load_dotenv()
    validate_env([
        "DATABASE_USERNAME",
        "DATABASE_PASSWORD",
        "DATABASE_HOSTNAME",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
    ])
    try:
        validate_db_schema()
    except Exception as exc:
        console.print(f"[yellow]DB schema validation warning:[/yellow] {exc}")


@app.command()
def chat():
    console.print("[bold]9fin SQL Agent[/bold]  •  type 'exit' to quit")
    while True:
        try:
            user = input("User: ").strip()
        except EOFError:
            break
        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            break
        answer = answer_question(user)
        console.print(Markdown(f"Agent: {answer}"))


if __name__ == "__main__":
    app()
