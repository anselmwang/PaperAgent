import requests
import json
import copy
import paper
import dataclasses
import jsonlines

@dataclasses.dataclass
class Response:
    score: int
    short_reason: str

    def to_json(self):
        return json.dumps(dataclasses.asdict(self))

def send_chat_message(paper: dict):
    paper = copy.copy(paper)
    assert "kimi_html_response" in paper, "kimi_html_response key not found in paper"
    del paper["kimi_html_response"]

    TEMPLATE = """Determine if the paper focuses on training Multimodal Large Language Models (LLMs). OUTPUT in below JSON format:
```
{"score": score, "short_reason": short_reason}
```
`score` is an integer between 0 and 10 to decide the relevance. 0 to be completely non-relevant, 10 to be perfectly relevant. `short_reason` is a short explanation.
- only work related to vision, video, and image processing is relevant. Work discussing other modalities like speech is considered score 0
- Only work related to Multimodal LLM application is relevant, multimodal LLM application is considered score 0

The paper is represented in json dict as below. 
```
%s
```
"""
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
    return Response(**json.loads(clean_response))

papers = paper.get_papers("2024-04-03")

for paper_dict in papers:
    response = send_chat_message(paper_dict)
    paper_dict['relevance'] = response.to_json()

with jsonlines.open('data/2024-04-03.classified.jsonl', mode='w') as writer:
    for paper_dict in papers:
        writer.write(paper_dict)
