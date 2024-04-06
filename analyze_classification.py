import jsonlines
import json

def load_classified_papers(filename):
    with jsonlines.open(filename) as reader:
        return [paper for paper in reader]

def count_papers_by_score(papers):
    score_counts = {score: 0 for score in range(11)}
    for paper in papers:
        relevance = json.loads(paper['relevance'])
        score_counts[relevance['score']] += 1
    return score_counts

def find_papers_with_score(papers, score):
    return [paper for paper in papers if json.loads(paper['relevance'])['score'] == score]

if __name__ == "__main__":
    classified_papers = load_classified_papers('data/2024-04-03.classified.jsonl')
    score_counts = count_papers_by_score(classified_papers)
    for score in range(11):
        print(f"Score {score}: {score_counts[score]} papers")
        papers_with_score = find_papers_with_score(classified_papers, score)
        for paper in papers_with_score:
            relevance = json.loads(paper['relevance'])
            print(f"Title: {paper['title']}, Reason: {relevance['short_reason']}")
