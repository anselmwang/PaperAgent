PaperAgent finds papers met your interests, a simple command `python retrieve_papers.py --task_name mllm_for_understanding_training --days 90 --min_score 5` creates `papers.epub` under current path following below steps:
- Retrieve the title, author, abstract, summarization of last 90 days' arxiv papers
- Call local ollama to score each paper according to specified task (in this example, the task is mllm_for_understanding_training, which is to find papers related to multi-modal large language model training)
- Keep only papers with score >= 5.
- Generate papers.epub, with nice organized 3 level table of content
    - top level: date
    - 2nd level: score
    - 3rd level: paper title

# Setup

Please setup ollama and retrieve mistral model in local machine first.

Then
```
pip install -r requirements.txt
```