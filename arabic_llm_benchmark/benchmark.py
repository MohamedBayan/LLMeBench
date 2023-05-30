import argparse

import importlib
import json
import logging
import sys
import traceback

from glob import glob
from pathlib import Path

import utils


class SingleTaskBenchmark(object):
    def __init__(
        self,
        config,
        prompt_fn,
        post_process_fn,
        cache_dir,
        ignore_cache=False,
        ignore_postprocessing=True,
        limit=-1,
    ):
        # Pipeline components
        self.dataset = config["dataset"](**config["dataset_args"])
        self.task = config["task"](self.dataset, **config["task_args"])
        self.model = config["model"](**config["model_args"])

        # Caching parameters
        self.cache_dir = cache_dir
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)
        self.ignore_cache = ignore_cache
        self.ignore_post_processing = ignore_postprocessing

        # Model inference
        self.prompt_fn = prompt_fn
        self.post_process_fn = post_process_fn

        # Data parameters
        self.data_path = config["general_args"]["data_path"]
        self.limit = limit

    def run_pipeline(self, sample_key, input_sample, cache_payload=None):
        # Prepare the prompt
        if "prompt" in cache_payload:
            logging.info(f"\tLoading prompt from cache")
            prompt = cache_payload["prompt"]
        else:
            logging.info(f"\tGenerating prompt")
            prompt = self.prompt_fn(input_sample)
            cache_payload["prompt"] = prompt

        # Run the model
        if "model_output" in cache_payload:
            logging.info(f"\tLoading model output from cache")
            model_output = cache_payload["model_output"]

        if "model_output" not in cache_payload or "response" not in model_output:
            logging.info(f"\tRunning model")
            model_output = self.model.run_model(**prompt)
            cache_payload["model_output"] = model_output

        if "response" not in model_output:
            return cache_payload

        if "filtered_output" in cache_payload and not self.ignore_post_processing:
            logging.info(f"\tLoading post processed output from cache")
            filtered_output = cache_payload["filtered_output"]
        else:
            logging.info(f"\tPost processing model outputs")
            try:
                filtered_output = self.post_process_fn(model_output["response"])
                cache_payload["filtered_output"] = filtered_output
            except Exception as e:
                exc_info = sys.exc_info()
                exception_str = "".join(traceback.format_exception(*exc_info))
                cache_payload["filtered_output_failure_message"] = exception_str

        return cache_payload

    def run_benchmark(self):
        data = self.task.load_data(self.data_path)

        true_labels = []
        predictions = []

        num_failed = 0
        for sample_idx, input_sample in enumerate(data):
            if self.limit > 0 and sample_idx >= self.limit:
                break
            logging.info(f"Running sample {sample_idx}: {input_sample['input']}")
            cache_path = self.cache_dir / f"{sample_idx}.json"
            true_labels.append(input_sample["label"])

            cache_payload = {"input": input_sample}
            if cache_path.exists() and not self.ignore_cache:
                with open(cache_path, "r") as fp:
                    cache_payload = json.load(fp)

            cache_payload = self.run_pipeline(
                sample_idx, input_sample["input"], cache_payload
            )
            if "filtered_output" in cache_payload:
                predictions.append(cache_payload["filtered_output"])
            else:
                logging.error(f"\tNo prediction for sample")
                num_failed += 1
                predictions.append(None)

            # Save the cache payload
            with open(cache_path, "w") as fp:
                json.dump(cache_payload, fp)

        if num_failed > 0:
            logging.error(
                f"{num_failed}/{len(data)} samples do not have any predictions"
            )
        evaluation_scores = self.task.evaluate(true_labels, predictions)

        return evaluation_scores


class Benchmark(object):
    def __init__(self, benchmark_dir):
        self.benchmark_dir = Path(benchmark_dir)

    def find_runs(self, filter_str):
        if not filter_str.endswith(".py"):
            filter_str += ".py"
        runs = []
        match_str = str(self.benchmark_dir / "**" / filter_str)
        for run in glob(match_str, recursive=True):
            module_path = str(Path(run).resolve())
            module_name = Path(run).name
            runs.append(
                {
                    "name": run[len(str(self.benchmark_dir)) + 1 : run.rfind(".")],
                    "path": run,
                    "module": utils.import_source_file(Path(module_path), module_name),
                }
            )

        return runs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_dir", type=Path)
    parser.add_argument("results_dir", type=Path)
    parser.add_argument(
        "-f",
        "--filter",
        default="*.py",
        help="Filter to match specific tasks in the benchmark. Examples are '*ZeroShot*', 'Demography*', '*.py' (default). The .py extension is added automatically if missing.",
    )
    parser.add_argument("--ignore_cache", action="store_true")
    parser.add_argument(
        "-l",
        "--limit",
        default=-1,
        type=int,
        help="Limit the number of input instances that will be processed",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    benchmark = Benchmark(args.benchmark_dir)

    runs = benchmark.find_runs(filter_str=args.filter)

    for run in runs:
        name = run["name"]
        config = run["module"].config()
        prompt_fn = run["module"].prompt
        post_process_fn = run["module"].post_process

        logging.info(f"Running benchmark: {name}")
        task_benchmark = SingleTaskBenchmark(
            config,
            prompt_fn,
            post_process_fn,
            cache_dir=args.results_dir / name,
            ignore_cache=args.ignore_cache,
            limit=args.limit,
        )

        print(task_benchmark.run_benchmark())


if __name__ == "__main__":
    main()
