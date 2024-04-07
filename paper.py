import json
import time
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

DATA_FOLDER = 'data/cool_papers_dump'
import dataclasses


@dataclasses.dataclass
class Response:
    score: int
    short_reason: str
@dataclasses.dataclass
class Paper:
    date: str
    title: str
    link: str
    authors: str
    abstract: str
    kimi_html_response: str = None
    relevance: Response = None

def dump_papers_to_jsonl(papers, filename):
    "dump the papers object to a JSONL file in the DATA_FOLDER"

    with open(f"{DATA_FOLDER}/{filename}", 'w', encoding='utf-8') as file:
        for paper_obj in papers:
            json.dump(dataclasses.asdict(paper_obj), file, ensure_ascii=False)
            file.write('\n')

def load_papers_from_jsonl(filename):
    "load papers from a JSONL file in the DATA_FOLDER"

    papers = []
    with open(f"{DATA_FOLDER}/{filename}", 'r', encoding='utf-8') as file:
        for line in file:
            paper_data = json.loads(line.strip())
            papers.append(Paper(**paper_data))
    return papers

# Function to extract paper details
def extract_paper_details(paper_div, date):
    title = paper_div.find('h2', class_='title').find('a', class_='title-link').get_text(strip=True)
    link = paper_div.find('h2', class_='title').find('a', href=True)['href']
    authors = ' ; '.join([author.get_text(strip=True) for author in paper_div.find('p', class_='authors').find_all('span', class_='author')])
    abstract = paper_div.find('p', class_='summary').get_text(strip=True)
    return Paper(date=date, title=title, link=link, authors=authors, abstract=abstract)

def get_kimi_content(url, retries=3, sleep_time=5):
    "fetch the content of the paper from the constructed URL with retry and sleep"

    for _ in range(retries):
        try:
            # Extract the paper id from the input URL
            paper_id = url.split('/')[-1]

            # Construct the new URL
            new_url = f"https://papers.cool/arxiv/kimi?paper={paper_id}"

            # Fetch the content of the new URL
            response = requests.get(new_url)

            # Check if the request was successful
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Error fetching Kimi content: {e}")
            time.sleep(sleep_time)

    return None

def fetch_html_content(url, retries=3, sleep_time=5):
    "fetch the HTML content from the constructed URL with retry and sleep"

    for _ in range(retries):
        try:
            # Fetch the content of the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Error fetching HTML content: {e}")
            time.sleep(sleep_time)

    return None

def extract_papers(date):
    # Construct the URL
    url = f"https://papers.cool/arxiv/cs.CV?date={date}&show=10000"

    # Fetch the HTML content
    html_content = fetch_html_content(url)

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the date
    date_text = soup.find('p', class_='info').find('a', class_='date').get_text(strip=True)
    # Convert the date to the required format
    date = datetime.strptime(date_text, '%a, %d %b %Y').strftime('%Y-%m-%d')

    # Extract the total number of papers
    total_papers_text = soup.find('p', class_='info').get_text(strip=True)
    total_papers = int(re.search(r'Total: (\d+)', total_papers_text).group(1))

    # Extract all papers and fetch Kimi content
    papers_divs = soup.find_all('div', class_='panel paper')
    papers = []
    for i, paper_div in enumerate(papers_divs):
        paper_obj = extract_paper_details(paper_div, date)
        paper_obj.kimi_html_response = get_kimi_content(paper_obj.link)
        papers.append(paper_obj)
        print(f"Extracted {i+1} of {total_papers} papers")

    # Verify the number of extracted papers
    assert len(papers) == total_papers, f"Extracted papers ({len(papers)}) does not match total reported ({total_papers})"

    return papers


def get_papers(date):
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    # Check if the file exists
    if os.path.exists(f"{DATA_FOLDER}/{date}.jsonl"):
        # Load papers from file
        papers = load_papers_from_jsonl(f"{date}.jsonl")
    else:
        # Extract papers and dump to file
        papers = extract_papers(date)
        dump_papers_to_jsonl(papers, f"{date}.jsonl")
    return papers

if __name__ == "__main__":
    DATE = '2024-04-03'
    papers = get_papers(DATE)

