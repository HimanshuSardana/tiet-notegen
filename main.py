from scraper.scrape import CourseScraper
from scraper.scrape import PaperScraper
from rich.prompt import Prompt
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.progress import Progress
import requests
import os
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()
console.print("[bold cyan]TIET Notegen[/bold cyan]")

subject_name = Prompt.ask("Enter the subject name (e.g., 'Data Structures')", default="Design and Analysis of Algorithms")
scraper = CourseScraper(subject_name)

with Live(Spinner("dots", text="Fetching courses"), console=console, transient=True):
    courses = scraper.fetch_courses()

if not courses:
    console.print("[bold red]No courses found for the given subject.[/bold red]")
else:
    # table
    table = Table(title=f"Search results for [bold]{subject_name}[/bold]")
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Course Name", style="magenta")

    for i, course in enumerate(courses, start=1):
        table.add_row(str(i), course)
    console.print(table)

course_index = Prompt.ask("Enter index of the course you want to scrape", default="1")
course_name = courses[int(course_index) - 1]

scraper = PaperScraper(course_name)

with Live(Spinner("dots", text="Fetching papers..."), console=console, transient=True):
    scraper.fetch_papers()

if not scraper.html_content:
    console.print("[bold red]No papers found or failed to fetch content.[/bold red]")
else:
    papers = scraper.parse_papers()
    if not papers:
        console.print("[bold red]No papers found for the selected course.[/bold red]")
    else:
        console.print(f"[bold green]Found {len(papers)} papers for {course_name}[/bold green]")

    """
    'subject_code': subject_code,
    'subject_name': subject_name,
    'year': year,
    'semester': semester,
    'type_of_paper': type_of_paper,
    'link': 'http://cl.thapar.edu/' + link
    """

    # make table
    table = Table(title=f"Papers for [bold]{course_name}[/bold]")
    table.add_column("Subject Code", style="cyan")
    table.add_column("Subject Name", style="magenta")
    table.add_column("Year", style="green")
    table.add_column("Semester", style="yellow")
    table.add_column("Type of Paper", style="blue")

    download_dir = f"./output/{course_name.replace(' ', '_')}"
    os.makedirs(download_dir, exist_ok=True)

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total}"),
    TimeRemainingColumn(),
    console=console
) as progress:
    download_task = progress.add_task("[cyan]Downloading papers...", total=len(papers))

    for paper in papers:
        url = paper["link"]
        filename = f"{paper['subject_code']}_{paper['year']}_{paper['semester']}_{paper['type_of_paper'].replace(' ', '_')}.pdf"
        filepath = os.path.join(download_dir, filename)

        try:
            response = requests.get(url, verify=False, stream=True, timeout=10)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            progress.update(download_task, advance=1)
        except Exception as e:
            console.print(f"[red]Failed to download:[/red] {filename} — {str(e)}")
            progress.update(download_task, advance=1)  # Still advance to not freeze

console.print(f"\n[bold green]Downloaded papers saved to:[/bold green] {download_dir}")
    
