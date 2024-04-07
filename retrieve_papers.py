import argparse
import datetime
from matcher import Matcher
import os
import paper
import dataclasses
import jsonlines
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

def main(task_name):
    current_date = start_date

    all_papers = []
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        papers = retrieve_papers(task_name, date_str)
        all_papers.extend(papers)
        current_date += datetime.timedelta(days=1)
    
    print(f"Total papers classified: {len(all_papers)}")

if __name__ == "__main__":
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Augment paper objects with relevance field.')
    parser.add_argument('task_name', type=str, help='Name of the task for relevance augmentation.')
    parser.add_argument('--days', type=int, help='Number of days to scrape.', required=False)
    args = parser.parse_args()
    if args.days:
        end_date = datetime.date.today() - datetime.timedelta(days=2)
        start_date = end_date - datetime.timedelta(days=args.days - 1)
    else:
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date.today() - datetime.timedelta(days=2)
    parser = argparse.ArgumentParser(description='Augment paper objects with relevance field.')
    parser.add_argument('task_name', type=str, help='Name of the task for relevance augmentation.')
    args = parser.parse_args()
    main(args.task_name)
