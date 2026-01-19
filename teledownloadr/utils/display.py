from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn, TotalFileSizeColumn

import questionary

class TUI:
    def __init__(self):
        self.console = Console()

    def print_banner(self):
        title = Text("TeleDownloadr", style="bold magenta")
        subtitle = Text("Media Downloader", style="italic white")
        
        panel = Panel(
            Text.assemble(title, "\n", subtitle, justify="center"),
            border_style="cyan",
            expand=False,
            padding=(1, 5)
        )
        self.console.print(panel, justify="center")
        self.console.print()

    def print_success(self, message: str):
        self.console.print(f"[bold green]✔[/] {message}")

    def print_error(self, message: str):
        self.console.print(f"[bold red]✖[/] {message}")
    
    def print_info(self, message: str):
        self.console.print(f"[bold cyan]ℹ[/] {message}")

    async def ask_choice(self, message: str, choices: list[str]) -> str:
        return await questionary.select(
            message,
            choices=choices
        ).ask_async()
    
    async def ask_text(self, message: str, default: str = "") -> str:
        return await questionary.text(message, default=default).ask_async()
    
    async def ask_checkbox(self, message: str, choices: list[str], instruction: str = None, use_shortcuts: bool = False, enable_search: bool = False) -> list[str]:
        """
        Ask user to select multiple items from a list.

        Args:
            message: The question to ask
            choices: List of choices
            instruction: Instruction text to display
            use_shortcuts: If False (default), disables keyboard shortcuts
            enable_search: If True, provides search before checkbox (for large lists)

        Returns:
            List of selected choices
        """
        if enable_search and len(choices) > 20:
            # For large lists, offer search first using simple text input
            self.console.print(f"[cyan]ℹ[/] {len(choices)} items available.")
            self.console.print(f"[dim]Type keywords to filter, or leave empty to see all.[/]")

            # Use simple text input instead of autocomplete (more reliable)
            search_query = await questionary.text(
                "Search filter (or press Enter for all):",
                default=""
            ).ask_async()

            if search_query and search_query.strip():
                # Filter choices based on search query (case-insensitive)
                search_lower = search_query.lower().strip()
                filtered = [c for c in choices if search_lower in c.lower()]

                if filtered:
                    self.console.print(f"[green]✔[/] Found {len(filtered)} matching items (filtered from {len(choices)} total)")

                    # Show checkbox with filtered results
                    return await questionary.checkbox(
                        message,
                        choices=filtered,
                        instruction=instruction
                    ).ask_async()
                else:
                    self.console.print(f"[yellow]![/] No matches found for '{search_query}'. Showing all items.")

        # Standard checkbox (no search or search skipped)
        return await questionary.checkbox(
            message,
            choices=choices,
            instruction=instruction
        ).ask_async()
    
    async def ask_confirm(self, message: str) -> bool:
        return await questionary.confirm(message).ask_async()

    def create_progress(self):
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TransferSpeedColumn(),
            TotalFileSizeColumn(),
            TimeRemainingColumn(),
            console=self.console
        )

# Global instance
tui = TUI()
