import requests
import json
from bs4 import BeautifulSoup

class CourseScraper:
    def __init__(self, subject_name):
        self.subject_name = subject_name
        subject_name = subject_name.replace(" ", "+").lower()
        self.base_url = f'http://cl.thapar.edu/search2.php?term={subject_name}'

    def fetch_courses(self):
        """
        Fetches courses from the Thapar University website for the given subject.
        """
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

        response = requests.get(self.base_url, headers=headers)
        return response.json()

class PaperScraper:
    def __init__(self, subject_name):
        self.subject_name = subject_name
        self.base_url = 'http://cl.thapar.edu/view2.php'
        self.html_content = None
        self.paper_data = []

    def fetch_papers(self):
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
                f'{self.subject_name}\r\n'
                '-----------------------------649919732726002793852520379430\r\n'
                'Content-Disposition: form-data; name="submit"\r\n\r\n\r\n'
                '-----------------------------649919732726002793852520379430--\r\n'
        )

        response = requests.post(self.base_url, headers=headers, data=data)
        self.html_content = response.text if response.status_code == 200 else None

    def parse_papers(self):
        """
        Parses the HTML content to extract paper links.
        """
        soup = BeautifulSoup(self.html_content, 'html.parser')
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
        self.paper_data = paper_data
        return paper_data


