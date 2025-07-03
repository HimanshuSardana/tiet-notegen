from src.scraper.scrape import CourseScraper
import json
from src.json2md.converter import Converter
from src.scraper.scrape import PaperScraper
from src.ocr.question2text import Question2Text
from src.classifier.classify import Classifier
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

question_papers_dir = f"./output/question_papers/COMPUTER_NETWORKS/"
text_files_dir = "./output/text_files/COMPUTER_NETWORKS/"

console = Console()
console.print("[bold cyan]TIET Notegen[/bold cyan]")

subject_name = Prompt.ask("Enter the subject name", default="Computer Networks")
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

clean_course_name = course_name.replace(' ', '_')

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

    download_dir = f"./output/question_papers/{course_name.replace(' ', '_')}"
    os.makedirs(download_dir, exist_ok=True)
    question_papers_dir = f"./output/question_papers/{course_name.replace(' ', '_')}"
    text_files_dir = f"./output/text_files/{course_name.replace(' ', '_')}"

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

console.print(f"[bold green]Downloaded papers saved to:[/bold green] {download_dir}")

question_to_text = Question2Text(question_papers_dir, text_files_dir)

with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TextColumn("{task.completed}/{task.total}"), TimeRemainingColumn(), console=console) as progress:
    convert_task = progress.add_task("[cyan]Converting PDFs to text...", total=len(os.listdir(question_papers_dir)))
    question_to_text.convert_pdfs_to_text()
    progress.update(convert_task, advance=len(os.listdir(question_papers_dir)))

console.print(f"[bold green]Converted PDFs to text files in:[/bold green] {text_files_dir}")

classifier = Classifier()
text_files = [filename for filename in os.listdir(text_files_dir) if filename.endswith(".txt")]

os.makedirs(f"./output/{clean_course_name}", exist_ok=True)

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total}"),
    TimeRemainingColumn(),
    console=console
) as progress:
    classify_task = progress.add_task("[cyan]Classifying questions...", total=len(text_files))

    final_data = {}
    for filename in text_files:
        with open(os.path.join(text_files_dir, filename), "r", encoding="utf-8") as file:
            content = file.read()
            prompt = classifier.build_prompt(content, final_data)
            response_text = classifier.generate_text(prompt)
            new_data = classifier.clean_json(response_text)

            for topic, questions in new_data.items():
                if topic not in final_data:
                    final_data[topic] = []
                for q in questions:
                    if q not in final_data[topic]:
                        final_data[topic].append(q)

        json.dump(final_data, open(f"./output/{clean_course_name}/classified_questions.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        progress.update(classify_task, advance=1)

console.print("[bold green]Classification completed![/bold green]")

converter = Converter(f"./output/{clean_course_name}/classified_questions.json", f"./output/{clean_course_name}/classified_questions.md")
# markdown_content = converter.convert_json()
# console.print(f"[bold green]Converted JSON to Markdown:[/bold green] {converter.markdown_file_path}")

converter.convert_to_typst(f"./output/{clean_course_name}/classified_questions.typ")

