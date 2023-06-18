import os
import random
import re

from arabic_llm_benchmark.datasets import FactualityUnifiedFCDataset
from arabic_llm_benchmark.models import GPTChatCompletionModel
from arabic_llm_benchmark.tasks import FactualityUnifiedFCTask


random.seed(1333)


def config():
    return {
        "dataset": FactualityUnifiedFCDataset,
        "dataset_args": {},
        "task": FactualityUnifiedFCTask,
        "task_args": {},
        "model": GPTChatCompletionModel,
        "model_args": {
            "api_type": "azure",
            "api_version": "2023-03-15-preview",
            "api_base": os.environ["AZURE_API_URL"],
            "api_key": os.environ["AZURE_API_KEY"],
            "engine_name": os.environ["ENGINE_NAME"],
            "class_labels": ["true", "false"],
            "max_tries": 30,
        },
        "general_args": {
            "data_path": "data/factuality_disinformation_harmful_content/factuality_stance_ramy/ramy_arabic_fact_checking.tsv"
        },
    }


def prompt(input_sample):
    prompt_string = (
        f'Annotate the "text" into one of the following categories: correct or incorrect\n\n'
        f"text: {input_sample}\n"
        f"label: \n"
    )
    return [
        {
            "role": "system",
            "content": "You are a news analyst and you can check the information in the news article and annotate them.",  # You are capable of identifying and annotating tweets correct or incorrect
        },
        {
            "role": "user",
            "content": prompt_string,
        },
    ]


def post_process(response):
    label = response["choices"][0]["message"]["content"].lower()
    # label_fixed = label.replace("label:", "").strip()

    if (
        label.startswith("I am unable to verify".lower())
        or label.startswith("I am unable to categorize".lower())
        or label.startswith(
            "I am an AI language model and I am unable to verify".lower()
        )
    ):
        label_fixed = None
    elif "label: incorrect" in label or "incorrect" in label:
        label_fixed = "False"
    elif "label: correct" in label or "correct" in label:
        label_fixed = "True"
    else:
        label_fixed = None

    return label_fixed