import os

from arabic_llm_benchmark.datasets import CheckworthinessDataset
from arabic_llm_benchmark.models import BLOOMPetalModel
from arabic_llm_benchmark.tasks import CheckworthinessTask


def config():
    return {
        "dataset": CheckworthinessDataset,
        "dataset_args": {},
        "task": CheckworthinessTask,
        "task_args": {},
        "model": BLOOMPetalModel,
        "model_args": {
            "api_url": os.environ["API_URL"],
            "class_labels": ["0", "1"],
            "max_tries": 3,
        },
        "general_args": {
            "data_path": "data/factuality_disinformation_harmful_content/checkworthyness/dutch/CT22_dutch_1A_checkworthy_test_gold.tsv"
        },
    }


def prompt(input_sample):
    return {
        "prompt": "Classify the tweet as checkworthy or not checkworthy. Provide only label.\n\n"
        + "tweet: "
        + input_sample
        + "label: \n"
    }


def post_process(response):
    label = response["outputs"].strip().lower()
    label = label.replace("<s>", "")
    label = label.replace("</s>", "")

    label_fixed = None

    if label == "checkworthy":
        label_fixed = "1"
    elif (
        label == "Not_checkworthy."
        or label == "not_checkworthy"
        or label == "not checkworthy"
    ):
        label_fixed = "0"

    return label_fixed
