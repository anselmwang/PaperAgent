import requests
import dataclasses
import copy
import paper
import dataclasses
import jsonlines
from tqdm import tqdm
import json
from paper import Paper, Response



class Matcher:

    TEMPLATE = """Determine how relevant the paper is. OUTPUT in JSON format: `{"score": score, "short_reason": short_reason}`.
`score` is an integer between 0 and 10 to decide the relevance. 0 to be completely non-relevant, 10 to be perfectly relevant. `short_reason` is a short explanation.

A paper is relevant only when it matches the following criteria simultaneously:
%(criteria)s

The paper is represented in json dict as below. 
```
%(paper)s
```
"""

    def __init__(self, task: str):
        with open(f"tasks/{task}.criteria.txt", 'r') as file:
            self.criteria = file.read()

    def match(self, paper: Paper):
        paper_copy = copy.copy(paper)
        assert paper_copy.kimi_html_response is not None, "kimi_html_response key not found in paper"
        paper_dict = dataclasses.asdict(paper_copy)
        del paper_dict["kimi_html_response"]

        message = self.TEMPLATE % {"criteria": self.criteria, "paper": json.dumps(paper_dict)}

        url = 'http://localhost:11434/api/chat'
        headers = {'Content-Type': 'application/json'}
        payload = {
            'model': "mistral",
            'messages': [{"role": "user", "content": message}],
            'stream': False,
            "format": "json"
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        clean_response = response.json()["message"]["content"]
        response_data = json.loads(clean_response)
        return Response(score=response_data['score'], short_reason=response_data['short_reason'])

def classify_papers(task, date):
    matcher = Matcher(task)
    papers = paper.get_papers(date)

    for paper_obj in tqdm(papers, desc="Classifying papers"):
        response = matcher.match(paper_obj)
        paper_obj.relevance = response

    with jsonlines.open(f'data/tasks/{task}/{date}.jsonl', mode='w') as writer:
        for paper_obj in papers:
            writer.write(dataclasses.asdict(paper_obj))
    
    return papers

task = "mllm_training"
date = "2024-04-03"
classify_papers(task, date)
