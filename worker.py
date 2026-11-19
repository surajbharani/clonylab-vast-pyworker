"""PyWorker for Vast Serverless: tells Vast how to talk to the Clonylab voice server (lab/server.py) that onstart.sh starts on the worker.
Needs a PUBLIC git repo that holds this file and requirements.txt (Vast clones it from the template's PYWORKER_REPO variable).
NOT TESTED YET: written from Vast's docs (docs.vast.ai/guides/serverless/creating-new-pyworkers) on 2026-11-19."""
from vastai import BenchmarkConfig, HandlerConfig, LogActionConfig, Worker, WorkerConfig

MODEL_SERVER_URL = "http://127.0.0.1"
MODEL_SERVER_PORT = 18000  # onstart.sh starts the voice server here
MODEL_LOG_FILE = "/var/log/clonylab/server.log"


def benchmark_payload() -> dict:
    # A short English voice-over with no recording needed (voice design), so the worker can be measured before any voice is prepared.
    return {"mode": "design", "text": "This is a short test of the Clonylab voice server on a new worker.", "language": "en", "instruct": "female, american accent", "num_step": 8}


def workload(payload: dict) -> float:
    # How much work a request is: characters times decoding steps (a long text at 32 steps counts more than a short one at 8).
    return float(len(str(payload.get("text", ""))) * int(payload.get("num_step", 32) or 32))


worker_config = WorkerConfig(
    model_server_url=MODEL_SERVER_URL,
    model_server_port=MODEL_SERVER_PORT,
    model_log_file=MODEL_LOG_FILE,
    handlers=[
        HandlerConfig(
            route="/generate",
            allow_parallel_requests=True,  # the voice server groups waiting requests into one batch (up to 8)
            max_queue_time=60.0,
            workload_calculator=workload,
            benchmark_config=BenchmarkConfig(generator=benchmark_payload, runs=4, concurrency=4),
        ),
    ],
    log_action_config=LogActionConfig(
        on_load=["CLONYLAB-MODEL-LOADED"],
        on_error=["Traceback (most recent call last):", "RESTORE-FAILED"],
        on_info=[],
    ),
)

Worker(worker_config).run()
