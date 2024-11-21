from llmebench.datasets import OSACT4SubtaskADataset
from llmebench.models import AzureModel
from llmebench.tasks import OffensiveTask


def metadata():
    return {
        "author": "Mohamed Bayan Kmainasi, Rakif Khan, Ali Ezzat Shahroor, Boushra Bendou, Maram Hasanain, and Firoj Alam",
        "affiliation": "Arabic Language Technologies, Qatar Computing Research Institute (QCRI), Hamad Bin Khalifa University (HBKU)",
        "model": "Llama-3.1-8B-Instruct",
        "description": "For a comprehensive analysis and results, refer to our peer-reviewed publication available at [Springer](https://doi.org/10.1007/978-981-96-0576-7_30) or explore the preprint version on [arXiv](https://arxiv.org/abs/2409.07054).",
    }


def config():
    return {
        "dataset": OSACT4SubtaskADataset,
        "task": OffensiveTask,
        "model": AzureModel,
        "model_args": {
            "class_labels": ["OFF", "NOT_OFF"],
            "max_tries": 1,
        },
    }


def prompt(input_sample):
    return [
        {
            "role": "user",
            "content": (
                f"يرجى تقييم الجملة التالية لتحديد ما إذا كانت تحتوي على محتوى مسيء. إذا كانت الجملة تحتوي على أي درجة من الإساءة، قم بالرد بـ 'OFF'. إذا لم تحتوي الجملة على أي محتوى مسيء أو مهين أو ضار، قم بالرد بـ 'NOT_OFF'.:\n{input_sample}"
            ),
        }
    ]


def post_process(response):
    print(response)
    if not response or "output" not in response:
        print("Error or missing output in response:", response)
        return "NOT_OFF"  # Safely default to "NOT_OFF" when unsure

    label = response["output"]
    label = label.lower()
    print("label", label)

    if (
        "not" in label
        or "غير" in label
        or "ليس" in label
        or "لا تحتوي" in label
        or "NOT" in label
        or "'not_off'" in label
    ):
        return "NOT_OFF"
    elif "off" in label:
        return "OFF"
    else:
        return None