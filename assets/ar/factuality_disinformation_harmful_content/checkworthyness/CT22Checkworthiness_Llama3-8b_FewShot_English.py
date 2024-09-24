import re

from llmebench.datasets import CT22CheckworthinessDataset
from llmebench.models import AzureModel
from llmebench.tasks import CheckworthinessTask


def metadata():
    return {
        "author": "Arabic Language Technologies, QCRI, HBKU",
        "model": "LLama3-8b",
        "description": "Deployed on Azure.",
        "scores": {"F1 (POS)": "0.554"},
    }


def config():
    return {
        "dataset": CT22CheckworthinessDataset,
        "task": CheckworthinessTask,
        "model": AzureModel,
        "model_args": {
            "class_labels": ["0", "1"],
            "max_tries": 100,
        },
        "general_args": {"test_split": "ar", "fewshot": {"train_split": "ar"}},
    }


def few_shot_prompt(input_sample, base_prompt, examples):
    out_prompt = base_prompt + "\n"
    out_prompt = out_prompt + "These are some examples:\n\n"
    for index, example in enumerate(examples):
        label = "not checkworthy" if example["label"] == "0" else "checkworthy"

        out_prompt = (
            out_prompt
            + "Example "
            + str(index)
            + ":\n"
            + "Tweet: "
            + example["input"]
            + "\n"
            + "Classification: "
            + label
            + "\n\n"
        )

    out_prompt = out_prompt + "Tweet: " + input_sample + "\nClassification: \n"

    return out_prompt


def prompt(input_sample, examples):
    base_prompt = 'Classify the tweet as "checkworthy" or "not checkworthy". Provide the classification only for the last tweet, without providing any additional justification:\n'
    return [
        {
            "role": "user",
            "content": few_shot_prompt(input_sample, base_prompt, examples),
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
        "not" in label
        or "غير" in label
        or "no" in label
        or "ليس" in label
        or "ليست" in label
    ):
        return "0"
    return "1"
    return label
