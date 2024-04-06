import json
import time
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os
import ebooklib.epub as epub

DATA_FOLDER = 'data'
import dataclasses

@dataclasses.dataclass
class Paper:
    date: str
    title: str
    link: str
    authors: str
    abstract: str
    kimi_html_response: str = None

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
    return {
        Paper(date=date, title=title, link=link, authors=authors, abstract=abstract)
    }

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
    url = f"https://papers.cool/arxiv/cs.CV?date={date}&show=300"

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
        papers.append(paper)
        print(f"Extracted {i+1} of {total_papers} papers")

    # Verify the number of extracted papers
    assert len(papers) == total_papers, f"Extracted papers ({len(papers)}) does not match total reported ({total_papers})"

    return papers

def create_epub(papers, filename):
    "create an epub file from the papers object"

    # Create a new epub book
    book = epub.EpubBook()

    # Set the book title and author
    book.set_title('Arxiv Papers')
    book.add_author('Arxiv')

    # Create the first level TOC - date
    date_chapter = epub.EpubHtml(title=papers[0]['date'], file_name='date.xhtml')
    date_chapter.content = f"<h1>{papers[0]['date']}</h1>"
    book.add_item(date_chapter)

    # Create the second level TOC - papers
    paper_chapters = []
    for paper in papers:
        paper_chapter = epub.EpubHtml(title=paper['title'], file_name=f"{paper['link'].split('/')[-1]}.xhtml")
        paper_chapter.content = f"<h2>{paper.title}</h2><p>Authors: {paper.authors}</p><p>Abstract: {paper.abstract}</p><p>Link: <a href='{paper.link}'>{paper.link}</a></p><p>Kimi HTML Response: {paper.kimi_html_response}</p>"
        book.add_item(paper_chapter)
        paper_chapters.append(paper_chapter)

    # Create the TOC
    book.toc = [(date_chapter, paper_chapters)]

    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

    # Add CSS file
    book.add_item(nav_css)

    # Create spine
    book.spine = ['nav', date_chapter] + paper_chapters

    # Write the epub file
    epub.write_epub(filename, book, {})



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

# DATE = '2024-04-03'
# papers = get_papers(DATE)
# # Create an epub file from the papers object
# create_epub(papers, f"{DATE}.epub")

# print(f"EPUB file created: {DATE}.epub")
