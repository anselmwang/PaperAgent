import argparse
import datetime
from matcher import Matcher
import os
import paper
import dataclasses
import jsonlines
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from tqdm import tqdm
from paper import Paper, Response

def retrieve_papers(task, date):
    matcher = Matcher(task)
    task_folder_path = f'data/tasks/{task}'
    if not os.path.exists(task_folder_path):
        os.makedirs(task_folder_path)
    classified_papers_path = f'{task_folder_path}/{date}.jsonl'
    classified_papers_path = f'data/tasks/{task}/{date}.jsonl'
    if os.path.exists(classified_papers_path):
        with jsonlines.open(classified_papers_path, mode='r') as reader:
            papers = [Paper(**{**obj, 'relevance': Response(**obj['relevance'])}) for obj in reader]
    else:
        papers = paper.get_papers(date)
        for paper_obj in tqdm(papers, desc="Classifying papers"):
            response = matcher.match(paper_obj)
            paper_obj.relevance = response
        with jsonlines.open(classified_papers_path, mode='w') as writer:
            for paper_obj in papers:
                writer.write(dataclasses.asdict(paper_obj))
    
    return papers

def main(task_name, start_date, end_date):
    current_date = start_date

    all_paper_dict = {}
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        papers = retrieve_papers(task_name, date_str)
        all_paper_dict[date_str] = papers
        current_date += datetime.timedelta(days=1)

    # Generate EPUB
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('Paper Collection')
    book.set_language('en')
    book.add_author('Paper Repository')

    # Sort dates in ascending order
    sorted_dates = sorted(all_paper_dict.keys())
    for date in sorted_dates:
        # Create a section for the date
        date_section = epub.EpubHtml(title=date, file_name=f'{date}.xhtml', lang='en')
        date_section.content = f'<h1>Papers for {date}</h1>'
        book.add_item(date_section)
        book.spine.append(date_section)

        # Group papers by score
        score_groups = {}
        for paper in all_paper_dict[date]:
            score = paper.relevance.score
            if score not in score_groups:
                score_groups[score] = []
            score_groups[score].append(paper)

        # Sort scores in descending order and create a TOC entry for each score
        date_toc = []
        for score in sorted(score_groups.keys(), reverse=True):
            score_section = epub.Section(f'Score: {score}')
            score_toc = []

            # Sort papers by title for each score
            for paper in sorted(score_groups[score], key=lambda p: p.title):
                # Create a chapter for each paper
                chapter = epub.EpubHtml(title=paper.title, file_name=f'{paper.title}.xhtml', lang='en')
                chapter.content = f'<h2><a href="{paper.link}">{paper.title}</a></h2>'
                chapter.content += f'<p>Authors: {paper.authors}</p>'
                chapter.content += f'<p>Score: {paper.relevance.score}</p>'
                chapter.content += f'<p>Reason: {paper.relevance.short_reason}</p>'
                chapter.content += f'<div>{BeautifulSoup(paper.kimi_html_response, "html.parser").prettify()}</div>'
                chapter.content += f'<p>Abstract: {paper.abstract}</p>'
                book.add_item(chapter)
                book.spine.append(chapter)
                score_toc.append(epub.Link(f'{paper.title}.xhtml', paper.title, f'score_{score}_{paper.title}'))
            date_toc.append((score_section, tuple(score_toc)))
        book.toc.append((epub.Link(f'{date}.xhtml', date, f'date_{date}'), tuple(date_toc)))

    # Define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Add navigation files
    book.spine = ['nav'] + sorted_dates
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Write the EPUB file
    epub.write_epub('papers.epub', book, {})



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Augment paper objects with relevance field.')
    parser.add_argument('--task_name', type=str, default="mllm_training", help='Name of the task for relevance augmentation.')
    parser.add_argument('--days', type=int, help='Number of days to scrape.', required=False)
    args = parser.parse_args()
    if args.days:
        end_date = datetime.date.today() - datetime.timedelta(days=2)
        start_date = end_date - datetime.timedelta(days=args.days - 1)
    else:
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date.today() - datetime.timedelta(days=2)

    main(args.task_name, start_date, end_date)
