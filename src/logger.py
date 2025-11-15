"""
Enhanced logging system with progress tracking and auto-scrolling logs.

Save this file as: src/logger.py
"""
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from collections import deque
from datetime import datetime
import sys

class Logger:
    """
    A logger that provides progress tracking and auto-scrolling log messages.
    """
    
    def __init__(self, verbose: bool = False, max_log_lines: int = 10):
        """
        Initialize the logger.
        
        Args:
            verbose (bool): Enable verbose logging
            max_log_lines (int): Maximum number of log lines to display before scrolling
        """
        self.verbose = verbose
        self.console = Console()
        self.max_log_lines = max_log_lines
        self.log_buffer = deque(maxlen=max_log_lines)
        self.live = None
        self.progress = None
        self.current_task = None
        self.layout = None
        
    def start(self):
        """Start the live display with progress bar and log area."""
        # Create progress bar
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        
        # Create layout
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="progress", size=3),
            Layout(name="logs", ratio=1)
        )
        
        # Start live display
        self.live = Live(self.layout, console=self.console, refresh_per_second=4)
        self.live.start()
        
    def stop(self):
        """Stop the live display."""
        if self.live:
            self.live.stop()
            self.live = None
            
    def add_task(self, description: str, total: int) -> int:
        """
        Add a progress task.
        
        Args:
            description (str): Task description
            total (int): Total number of items to process
            
        Returns:
            int: Task ID
        """
        if self.progress:
            self.current_task = self.progress.add_task(description, total=total)
            self._update_display()
            return self.current_task
        return None
        
    def update_task(self, task_id: int, advance: int = 1, description: str = None):
        """
        Update a progress task.
        
        Args:
            task_id (int): Task ID to update
            advance (int): Number of items to advance
            description (str): New description (optional)
        """
        if self.progress and task_id is not None:
            if description:
                self.progress.update(task_id, advance=advance, description=description)
            else:
                self.progress.update(task_id, advance=advance)
            self._update_display()
            
    def _update_display(self):
        """Update the live display with current progress and logs."""
        if self.layout and self.progress:
            # Update progress section
            self.layout["progress"].update(Panel(self.progress, title="Progress", border_style="blue"))
            
            # Update logs section
            log_table = Table.grid(padding=(0, 1))
            log_table.add_column(style="dim", width=8)
            log_table.add_column()
            
            for timestamp, level, message in self.log_buffer:
                log_table.add_row(timestamp, message)
            
            self.layout["logs"].update(Panel(log_table, title="Logs", border_style="green"))
            
    def _add_log(self, level: str, message: str, style: str = ""):
        """
        Add a log message to the buffer.
        
        Args:
            level (str): Log level (INFO, DEBUG, WARNING, ERROR)
            message (str): Log message
            style (str): Rich style string
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        styled_message = Text(f"[{level}] {message}", style=style)
        self.log_buffer.append((timestamp, level, styled_message))
        
        if self.layout:
            self._update_display()
    
    def debug(self, message: str):
        """Log a debug message (only shown in verbose mode)."""
        if self.verbose:
            self._add_log("DEBUG", message, "dim cyan")
    
    def info(self, message: str):
        """Log an info message."""
        self._add_log("INFO", message, "green")
    
    def warning(self, message: str):
        """Log a warning message."""
        self._add_log("WARN", message, "yellow")
    
    def error(self, message: str):
        """Log an error message."""
        self._add_log("ERROR", message, "bold red")
    
    def success(self, message: str):
        """Log a success message."""
        self._add_log("SUCCESS", message, "bold green")
        
    def print(self, message: str, style: str = ""):
        """
        Print a message directly to console (bypasses the log buffer).
        
        Args:
            message (str): Message to print
            style (str): Rich style string
        """
        if self.live:
            self.live.stop()
            self.console.print(message, style=style)
            self.live.start()
        else:
            self.console.print(message, style=style)


class SimpleLogger:
    """
    A simpler logger without progress bars, just styled messages.
    Useful for commands that don't need progress tracking.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console()
    
    def debug(self, message: str):
        """Log a debug message (only shown in verbose mode)."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console.print(f"[dim]{timestamp}[/dim] [dim cyan][DEBUG][/dim cyan] {message}")
    
    def info(self, message: str):
        """Log an info message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [green][INFO][/green] {message}")
    
    def warning(self, message: str):
        """Log a warning message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [yellow][WARN][/yellow] {message}")
    
    def error(self, message: str):
        """Log an error message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold red][ERROR][/bold red] {message}")
    
    def success(self, message: str):
        """Log a success message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold green][SUCCESS][/bold green] {message}")
    
    def print(self, message: str, style: str = ""):
        """Print a message directly."""
        self.console.print(message, style=style)