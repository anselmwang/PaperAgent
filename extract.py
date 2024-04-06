import time
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Function to extract paper details
def extract_paper_details(paper_div):
    title = paper_div.find('h2', class_='title').find('a', class_='title-link').get_text(strip=True)
    link = paper_div.find('h2', class_='title').find('a', href=True)['href']
    authors = ' ; '.join([author.get_text(strip=True) for author in paper_div.find('p', class_='authors').find_all('span', class_='author')])
    abstract = paper_div.find('p', class_='summary').get_text(strip=True)
    return {
        "date": date,
        "title": title,
        "link": link,
        "authors": authors,
        "abstract": abstract
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

def extract_papers():
    # Load the HTML content
    html_path = 'Computer Vision and Pattern Recognition _ Cool Papers - Immersive Paper Discovery.html'
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

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
        paper = extract_paper_details(paper_div)
        paper['kimi_html_response'] = get_kimi_content(paper['link'])
        papers.append(paper)
        print(f"Extracted {i+1} of {total_papers} papers")

    # Verify the number of extracted papers
    assert len(papers) == total_papers, f"Extracted papers ({len(papers)}) does not match total reported ({total_papers})"

    return papers

papers = extract_papers()
print("Fetching Kimi content for the first paper")
# Fetch the content of the first paper
paper = papers[0]
url = paper['link']
kimi_content = get_kimi_content(url)
print(kimi_content)
