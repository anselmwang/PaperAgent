import jsonlines

def load_classified_papers(filename):
    with jsonlines.open(filename) as reader:
        return [paper for paper in reader]

def find_papers_with_score(papers, score):
    return [paper for paper in papers if json.loads(paper['relevance'])['score'] == score]

if __name__ == "__main__":
    classified_papers = load_classified_papers('data/2024-04-03.classified.jsonl')
    papers_with_score_5 = find_papers_with_score(classified_papers, 5)
    for paper in papers_with_score_5:
        print(paper)
