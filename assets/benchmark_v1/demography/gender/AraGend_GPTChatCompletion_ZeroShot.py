import os

from arabic_llm_benchmark.datasets import ArabGendDataset
from arabic_llm_benchmark.models import GPTChatCompletionModel
from arabic_llm_benchmark.tasks import DemographyGenderTask


def config():
    return {
        "dataset": ArabGendDataset,
        "dataset_args": {},
        "task": DemographyGenderTask,
        "task_args": {},
        "model": GPTChatCompletionModel,
        "model_args": {
            "api_type": "azure",
            "api_version": "2023-03-15-preview",
            "api_base": os.environ["AZURE_API_URL"],
            "api_key": os.environ["AZURE_API_KEY"],
            "engine_name": "gpt",
            "class_labels": ["m", "f"],
            "max_tries": 3,
        },
        "general_args": {"data_path": "data/demography/gender/gender-test.txt"},
    }


def prompt(input_sample):
    return [
        {
            "role": "system",
            "content": "You are an AI assistant that helps people find information.",
        },
        {
            "role": "user",
            "content": f"If the following person name can be considered as male, write 'm' without explnanation, and if it can be considered as female, write 'f' without explnanation.\n {input_sample}",
        },
    ]


def post_process(response):
    return response["choices"][0]["message"]["content"]