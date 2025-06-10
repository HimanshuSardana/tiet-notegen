import requests
import os
import re
from bs4 import BeautifulSoup
import pymupdf
from google import genai
import json

TERM = 'Design and Analysis of Algorithms'
# API_KEY = "AIzaSyBWVX8Vd-YjUeHiPnKRkjVrw0ZjkbMR9ec"
API_KEY = "AIzaSyDnJX_RrxiHiIEb8mnX4bgUnOpjIdW8BjU"

client = genai.Client(api_key=API_KEY)
def generate_text(prompt):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


def fetch_courses(term):
    term = term.replace(' ', '+')
    url = f'https://cl.thapar.edu/search2.php?term={term}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Referer': 'https://cl.thapar.edu/ques.php',
    }

    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def get_question_papers(sub_name):
    url = 'https://cl.thapar.edu/view2.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'multipart/form-data; boundary=---------------------------649919732726002793852520379430',
        'Origin': 'https://cl.thapar.edu',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Referer': 'https://cl.thapar.edu/ques.php',
    }

    data = (
        '-----------------------------649919732726002793852520379430\r\n'
        'Content-Disposition: form-data; name="cname"\r\n\r\n'
        f'{sub_name}\r\n'
        '-----------------------------649919732726002793852520379430\r\n'
        'Content-Disposition: form-data; name="submit"\r\n\r\n\r\n'
        '-----------------------------649919732726002793852520379430--\r\n'
    )

    response = requests.post(url, headers=headers, data=data)
    return response.text if response.status_code == 200 else None

def parse_question_papers(html):
    soup = BeautifulSoup(html, 'html.parser')
    paper_data = []

    for tr in soup.find_all('tr')[2:]:
        tds = tr.find_all('td')
        if len(tds) > 1:
            subject_code = tds[0].text.strip()
            subject_name = tds[1].text.strip()
            year = tds[2].text.strip()
            semester = tds[3].text.strip()
            type_of_paper = tds[4].text.strip()
            link = tds[5].find('a')['href'] if tds[5].find('a') else None

            paper_data.append({
                'subject_code': subject_code,
                'subject_name': subject_name,
                'year': year,
                'semester': semester,
                'type_of_paper': type_of_paper,
                'link': 'https://cl.thapar.edu/' + link
            })
    return paper_data

def download_papers(paper_data):
    for paper in paper_data:
        # download the paper
        response = requests.get(paper['link'])

        if response.status_code == 200:
            filename = f"{paper['subject_code']}_{paper['year']}_{paper['semester']}.pdf"
            filepath = os.path.join('question_papers', filename)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {filename}")

def extract_text():
    for question_paper in os.listdir('question_papers'):
        if question_paper.endswith('.pdf'):
            pdf_path = os.path.join('question_papers', question_paper)
            doc = pymupdf.open(pdf_path)
            doc_text = ''
            for page in doc:
                doc_text += page.get_text()
                with open(os.path.join('texts', question_paper[:-4] + '.txt'), 'w', encoding='utf-8') as text_file:
                    text_file.write(doc_text)
                print(f"Saved text for {question_paper}")
            doc.close()

sub_name = fetch_courses(TERM)[0]
print(sub_name)
soup = get_question_papers(sub_name)
paper_data = parse_question_papers(soup)
download_papers(paper_data)
extract_text()
# generate_summary()

def generate_summary():
    client = genai.Client(api_key=API_KEY)
    for text_file in os.listdir('texts'):
        if text_file.endswith('.txt'):
            with open(os.path.join('texts', text_file), 'r', encoding='utf-8') as file:
                content = file.read()
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"Summarize the following question paper content:\n\n{content}",
                )
                summary = response.text
                with open(os.path.join('summaries', text_file[:-4] + '_summary.txt'), 'w', encoding='utf-8') as summary_file:
                    summary_file.write(summary)
                print(f"Generated summary for {text_file}")


def clean_json_response(text):
    """
    Cleans LLM response by removing markdown formatting like ```json ... ```
    """
    text = text.strip()
    # Remove triple backticks and optional language identifiers
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()

def classify_questions():
    client = genai.Client(api_key=API_KEY)
    final_data = {}

    for text_file in os.listdir('texts'):
        if text_file.endswith('.txt'):
            with open(os.path.join('texts', text_file), 'r', encoding='utf-8') as file:
                content = file.read()

            prompt = (
                    "You are an assistant that classifies university exam questions into topics.\n"
                    "You will be given:\n"
                    "1. A new question paper.\n"
                    "2. The current JSON structure of previously classified questions.\n\n"
                    "Your task is to update the JSON with the new questions. Follow these rules:\n"
                    "- Merge similar topics into a single topic key.\n"
                    "- Some question may refer to figures or diagrams. If so, rephrase them to be self-contained without referring to any figures. Make up a question text that does not depend on any figure.\n"
                    "- For questions or subparts that are incomplete (e.g. 'i) Priority Queue'), rephrase them into full questions (e.g. 'Explain what a priority queue is.').\n"
                    "- Do NOT include sub-labels like (a), (b), (i), etc. in the question text.\n"
                    "- Remove duplicates across all topics.\n"
                    "- Do NOT wrap the output in triple backticks or provide any explanation. Output only valid, complete JSON.\n\n"
                    "- Order the topics into the order they must be studied in.\n"
                    "Format example:\n"
                    "{\n"
                    "  \"Topic A\": [\"What is memory management?\", \"Explain paging.\\nExplain segmentation.\"],\n"
                    "  \"Topic B\": [\"Define recursion.\", \"Differentiate between BFS and DFS.\"]\n"
                    "}\n\n"
                    f"New Question Paper:\n{content}\n\n"
                    f"Current JSON:\n{json.dumps(final_data, indent=2, ensure_ascii=False)}\n"
            )

            response = client.models.generate_content(
                model="gemini-2.0-flash",  
                contents=prompt
            )

            try:
                cleaned = clean_json_response(response.text)
                classified = json.loads(cleaned)
                final_data = classified
                print(f"Processed {text_file}")
            except Exception as e:
                print(f"Error processing {text_file}: {e}")

    # Save final merged JSON
    with open('all_papers_classified.json', 'w', encoding='utf-8') as outfile:
        json.dump(final_data, outfile, indent=2, ensure_ascii=False)

    print("✅ All papers classified into all_papers_classified.json")

classify_questions()

# def generate_notes():
#     GUIDELINES = """
#     Here are the guidelines for formatting the notes:
#     Bold: enclose the text in single asterisks, e.g., *bold text*
#     Italics: enclose the text in single underscores, e.g., _italic text_
#     Bullet points: use a hyphen followed by a space, e.g., - bullet point
#     Numbered lists: use a number followed by a period and space, e.g., 1. first item
#
#     DO NOT use any other formatting, just use the above guidelines.
#     NO HEADINGS
#     """
#     with open("./paper_notes/PMC212_2023_E_notes.txt") as f:
#         data = json.loads(f.read())
#         for topic, questions in data.items():
#             notes = generate_text(f"Generate notes for the following topic: {topic}, here are some questions for reference {questions}\n\n{GUIDELINES}")
#             print(f"Topic: {topic}")
#             for question in questions:
#                 print(f"- {question}")
#             print("\n")
#             print(f"Notes: {notes}\n")

# generate_notes()
