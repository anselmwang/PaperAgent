import argparse
import datetime
import re
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
    total_days = (end_date - start_date).days + 1
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"Retrieving papers for {date_str} ({total_days - (end_date - current_date).days}/{total_days})")
        papers = retrieve_papers(task_name, date_str)
        all_paper_dict[date_str] = papers
        current_date += datetime.timedelta(days=1)

    book = epub.EpubBook()
    book.set_title('Arxiv Papers')
    book.add_author('Arxiv')

    # Initialize an empty TOC and spine
    book_toc = []
    book_spine = ['nav']

    # Sort dates in ascending order
    sorted_dates = sorted(all_paper_dict.keys())
    for date in sorted_dates:
        date_chapter = epub.EpubHtml(title=date, file_name=f"{date}.xhtml", content=f"<h1>{date}</h1>")
        book.add_item(date_chapter)
        book_spine.append(date_chapter)

        # Group papers by score
        score_groups = {}
        for paper in all_paper_dict[date]:
            score = paper.relevance.score
            if score not in score_groups:
                score_groups[score] = []
            score_groups[score].append(paper)

        score_chapters = []
        for score in sorted(score_groups.keys(), reverse=True):
            score_chapter = epub.EpubHtml(title=f'Score: {score}', file_name=f'{date}_score_{score}.xhtml', lang='en')
            score_chapter.content = f'<h2>Score: {score}</h2>'
            book.add_item(score_chapter)
            book_spine.append(score_chapter)

            title_chapters = []
            for paper_index, paper in enumerate(score_groups[score]):
                # Create a chapter for each paper
                sanitized_title = re.sub(r'[^\w\s-]', '', paper.title).replace(' ', '_')
                chapter_file_name = f'{date}_{score}_{sanitized_title}_{paper_index}.xhtml'
                paper_chapter = epub.EpubHtml(title=paper.title, file_name=chapter_file_name, lang='en')
                paper_chapter.content = f'<h2><a href="{paper.link}">{paper.title}</a></h2>'
                paper_chapter.content += f'<p>Authors: {paper.authors}</p>'
                paper_chapter.content += f'<p>Score: {paper.relevance.score}</p>'
                paper_chapter.content += f'<p>Reason: {paper.relevance.short_reason}</p>'
                paper_chapter.content += f'<div>{BeautifulSoup(paper.kimi_html_response, "html.parser").prettify()}</div>'
                paper_chapter.content += f'<p>Abstract: {paper.abstract}</p>'
                book.add_item(paper_chapter)
                book_spine.append(paper_chapter)
                title_chapters.append(paper_chapter)

            score_chapters.append((score_chapter, title_chapters))
        book_toc.append((date_chapter, score_chapters))

    book.toc = book_toc
    book.spine = book_spine

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
