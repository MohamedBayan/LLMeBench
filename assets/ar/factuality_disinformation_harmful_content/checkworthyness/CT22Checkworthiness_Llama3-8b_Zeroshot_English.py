import re

from llmebench.datasets import CT22CheckworthinessDataset
from llmebench.models import AzureModel
from llmebench.tasks import CheckworthinessTask


def metadata():
    return {
        "author": "Arabic Language Technologies, QCRI, HBKU",
        "model": "LLama3-8b",
        "description": "Deployed on Azure.",
        "scores": {"F1 (POS)": "0.560"},
    }


def config():
    return {
        "dataset": CT22CheckworthinessDataset,
        "task": CheckworthinessTask,
        "model": AzureModel,
        "model_args": {
            "class_labels": ["0", "1"],
            "max_tries": 30,
        },
        "general_args": {"test_split": "ar"},
    }


def prompt(input_sample):
    base_prompt = 'Classify the tweet as "checkworthy" or "not checkworthy". Provide the classification only for the last tweet, without providing any additional justification:\n'
    return [
        {
            "role": "user",
            "content": base_prompt + input_sample,
        },
    ]


import random


def post_process(response):
    print(response)
    if "output" in response:
        # if "content" in response["messages"]:
        label = response["output"].strip()
        label = label.replace("<s>", "")
        label = label.replace("</s>", "")
    else:
        print("Response .. " + str(response))
        label = ""
    label = label.lower()
    if "لا أستطيع" in label or "I cannot" in label:
        return random.choice(["0", "1"])
    if (
        "لا" in label
        or "not" in label
        or "no" in label
        or "ليس" in label
        or "ليست" in label
    ):
        return "0"
    return "1"
    return label
