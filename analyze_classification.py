import jsonlines
import json
from paper import Response
from paper import Response, Paper

def load_classified_papers(filename):
    with jsonlines.open(filename) as reader:
        return [Paper(**{**paper, 'relevance': Response(**paper['relevance'])}) for paper in reader]

def count_papers_by_score(papers):
    score_counts = {score: 0 for score in range(11)}
    for paper in papers:
        score_counts[paper.relevance.score] += 1
    return score_counts

def find_papers_with_score(papers, score):
    return [paper for paper in papers if paper.relevance.score == score]

if __name__ == "__main__":
    classified_papers = load_classified_papers('data/2024-04-03.classified.jsonl')
    score_counts = count_papers_by_score(classified_papers)
    for score in range(10, -1, -1):
        print(f"# Score {score}: {score_counts[score]} papers")
        papers_with_score = find_papers_with_score(classified_papers, score)
        for paper in papers_with_score:
            print(f"Title: {paper.title}, Reason: {paper.relevance.short_reason if paper.relevance else 'N/A'}")
