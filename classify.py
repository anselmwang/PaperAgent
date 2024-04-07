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

    def __init__(self, criteria: str):
        pass

    def match(self, paper: Paper):
        paper_copy = copy.copy(paper)
        assert paper_copy.kimi_html_response is not None, "kimi_html_response key not found in paper"
        paper_dict = dataclasses.asdict(paper_copy)
        del paper_dict["kimi_html_response"]

def send_chat_message(paper: dict):


    message = TEMPLATE % json.dumps(paper)

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

papers = paper.get_papers("2024-04-03")

for paper_dict in tqdm(papers, desc="Classifying papers"):
    paper_obj = Paper(**paper_dict)
    response = send_chat_message(paper_obj)
    paper_obj.relevance = response

with jsonlines.open('data/2024-04-03.classified.jsonl', mode='w') as writer:
    for paper_dict in papers:
        writer.write(dataclasses.asdict(paper_dict))

