"""LION Q&A CLI - Interactive question answering using RAG."""

import argparse
import sys
import requests
import json
from typing import Optional
from pathlib import Path
from datetime import datetime

# Try to import rich for better formatting (optional)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Default API endpoint
DEFAULT_API_URL = "http://127.0.0.1:8001"


class LIONClient:
    """Client for interacting with LION Q&A API."""

    def __init__(self, api_url: str = DEFAULT_API_URL):
        self.api_url = api_url.rstrip("/")
        self.console = Console() if HAS_RICH else None
        self._verify_connection()

    def _verify_connection(self) -> bool:
        """Verify API is running."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        return False

    def ask(self, question: str, context: Optional[str] = None) -> dict:
        """
        Send a question to the API and get an answer.
        
        Args:
            question: The question to ask
            context: Optional context information
            
        Returns:
            Response dict with answer, confidence, and source
        """
        try:
            payload = {"question": question}
            if context:
                payload["context"] = context

            response = requests.post(
                f"{self.api_url}/ask",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "error": f"Connection error: Cannot reach API at {self.api_url}",
                "answer": None,
                "confidence": 0.0,
                "source": "error",
            }
        except requests.exceptions.Timeout:
            return {
                "error": "Request timeout: API took too long to respond",
                "answer": None,
                "confidence": 0.0,
                "source": "error",
            }
        except requests.exceptions.HTTPError as e:
            return {
                "error": f"HTTP error: {e.response.status_code} - {e.response.text}",
                "answer": None,
                "confidence": 0.0,
                "source": "error",
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "answer": None,
                "confidence": 0.0,
                "source": "error",
            }

    def print_response(self, question: str, response: dict) -> None:
        """Print formatted response."""
        if "error" in response:
            if HAS_RICH:
                self.console.print(f"❌ Error: {response['error']}", style="bold red")
            else:
                print(f"ERROR: {response['error']}")
            return

        if HAS_RICH:
            # Use rich formatting
            self.console.print()
            self.console.print(Panel(f"[bold cyan]Q:[/bold cyan] {question}", border_style="cyan"))
            
            self.console.print(Panel(
                response.get("answer", "No answer"),
                title="[bold green]Answer[/bold green]",
                border_style="green"
            ))
            
            # Create table for metadata
            table = Table(title="Metadata", show_header=True, header_style="bold magenta")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")
            
            confidence = response.get("confidence", 0.0)
            confidence_style = "green" if confidence > 0.5 else "yellow" if confidence > 0.3 else "red"
            table.add_row("Confidence", f"{confidence:.4f}", style=confidence_style)
            table.add_row("Source", response.get("source", "unknown"))
            
            self.console.print(table)
        else:
            # Plain text formatting
            print("\n" + "=" * 80)
            print(f"Q: {question}")
            print("-" * 80)
            print(f"A: {response.get('answer', 'No answer')}")
            print("-" * 80)
            print(f"Confidence: {response.get('confidence', 0.0):.4f}")
            print(f"Source: {response.get('source', 'unknown')}")
            print("=" * 80 + "\n")


def interactive_mode(client: LIONClient) -> None:
    """Run interactive Q&A mode."""
    if HAS_RICH:
        client.console.print("[bold cyan]LION Q&A System - Interactive Mode[/bold cyan]")
        client.console.print("[dim]Type 'exit' or 'quit' to exit, 'help' for help[/dim]\n")
    else:
        print("\n=== LION Q&A System - Interactive Mode ===")
        print("Type 'exit' or 'quit' to exit, 'help' for help\n")

    while True:
        try:
            question = input("🦁 Question: ").strip()

            if not question:
                continue

            if question.lower() in ("exit", "quit"):
                if HAS_RICH:
                    client.console.print("[yellow]Goodbye![/yellow]")
                else:
                    print("Goodbye!")
                break

            if question.lower() == "help":
                print_help()
                continue

            # Show typing indicator
            if HAS_RICH:
                client.console.print("[dim]Thinking...[/dim]")
            else:
                print("Thinking...")

            response = client.ask(question)
            
            client.print_response(question, response)

        except KeyboardInterrupt:
            if HAS_RICH:
                client.console.print("\n[yellow]Interrupted by user[/yellow]")
            else:
                print("\nInterrupted by user")
            break
        except EOFError:
            break


def single_question_mode(client: LIONClient, question: str, context: Optional[str] = None) -> None:
    """Run single question mode."""
    response = client.ask(question, context)
    client.print_response(question, response)

    # Exit with error code if there was an error
    if "error" in response:
        sys.exit(1)


def batch_mode(client: LIONClient, file_path: str) -> None:
    """Run batch mode - read questions from file."""
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        questions = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    questions.append(line)

        if not questions:
            print("No questions found in file")
            sys.exit(1)

        if HAS_RICH:
            client.console.print(f"[cyan]Processing {len(questions)} questions from {file_path}[/cyan]\n")
        else:
            print(f"\nProcessing {len(questions)} questions from {file_path}\n")

        results = []
        for i, question in enumerate(questions, 1):
            if HAS_RICH:
                client.console.print(f"[dim][{i}/{len(questions)}][/dim] {question}")
            else:
                print(f"[{i}/{len(questions)}] {question}")

            response = client.ask(question)
            results.append({
                "question": question,
                "response": response
            })

            # Small delay between requests
            import time
            if i < len(questions):
                time.sleep(0.5)

        # Save results with timestamp in app/cli folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cli_folder = Path(__file__).parent
        output_file = cli_folder / f"batch_results_{timestamp}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        if HAS_RICH:
            client.console.print(f"\n[green]✓[/green] Results saved to {output_file}")
        else:
            print(f"\nResults saved to {output_file}")

    except Exception as e:
        print(f"Error in batch mode: {e}")
        sys.exit(1)


def print_help() -> None:
    """Print help information."""
    help_text = """
LION Q&A System - Help

Interactive Mode Commands:
  exit, quit    - Exit the program
  help          - Show this help message

Single Question Mode:
  python -m app.cli.qa "Your question here"

Batch Mode (read questions from file):
  python -m app.cli.qa --batch questions.txt
  
  File format: one question per line
  Lines starting with # are treated as comments

Examples:
  python -m app.cli.qa -i
  python -m app.cli.qa "EU DEVO DECLARAR IMPOSTO DE RENDA?"
  python -m app.cli.qa --batch questions.txt
  python -m app.cli.qa "Your question" --api http://localhost:8001
"""
    print(help_text)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LION Q&A System - Interactive RAG-based Question Answering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.cli.qa -i                    # Interactive mode
  python -m app.cli.qa "Your question"       # Single question
  python -m app.cli.qa --batch questions.txt # Batch mode
  python -m app.cli.qa "Q?" --api http://localhost:8001  # Custom API URL
        """,
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask (if not provided, enters interactive mode)",
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive mode",
    )

    parser.add_argument(
        "-b",
        "--batch",
        metavar="FILE",
        help="Batch mode - read questions from file",
    )

    parser.add_argument(
        "-c",
        "--context",
        help="Optional context information",
    )

    parser.add_argument(
        "--api",
        default=DEFAULT_API_URL,
        help=f"API endpoint URL (default: {DEFAULT_API_URL})",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    args = parser.parse_args()

    # Initialize client
    client = LIONClient(api_url=args.api)

    # Check if API is reachable
    if not client._verify_connection():
        print(f"Error: Cannot reach API at {args.api}")
        print(f"Make sure the server is running:")
        print(f"  cd /home/decode/workspace/lion")
        print(f"  source venv/bin/activate")
        print(f"  uvicorn app.api.app:app --host 127.0.0.1 --port 8001")
        sys.exit(1)

    # Determine mode
    if args.batch:
        batch_mode(client, args.batch)
    elif args.interactive or (not args.question and not sys.stdin.isatty()):
        interactive_mode(client)
    elif args.interactive or not args.question:
        interactive_mode(client)
    else:
        single_question_mode(client, args.question, args.context)


if __name__ == "__main__":
    main()
