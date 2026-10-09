import atexit
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory

from src.core import ResultContainer
from src.orchestration import ALGORITHMS, prepare_initial_state, run_algorithm, state_rows


RESULTS_FILE = Path(os.environ.get("IF3170_RESULTS_FILE", "output/results.pkl"))
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
MAX_WORKERS = max(2, min(8, os.cpu_count() or 4))

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
jobs_lock = Lock()
jobs = {}
futures = {}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def load_result_container():
    if not RESULTS_FILE.exists():
        return ResultContainer()

    try:
        return ResultContainer.loadFromFile(RESULTS_FILE)
    except Exception as error:
        print(f"Could not load {RESULTS_FILE}: {error}")
        return ResultContainer()


result_container = load_result_container()


def normalize_saved_results():
    algorithm_runs = {}

    for index, result in enumerate(result_container, start=1):
        if result.run_id is None:
            result.run_id = index
        if result.experiment_name is None:
            result.experiment_name = result.algorithm

        group = (result.algorithm, result.experiment_name)
        algorithm_runs[group] = algorithm_runs.get(group, 0) + 1

        if result.run_number is None:
            result.run_number = algorithm_runs[group]

        job_id = f"saved-{result.run_id}"
        jobs[job_id] = {
            "id": job_id,
            "status": "completed",
            "saved": True,
            "config": {
                "algorithm": result.algorithm,
                "experiment_name": result.experiment_name,
                "seed": result.metrics.get("seed", 42),
                "package_count": len(result.problem.packages),
                "truck_count": len(result.problem.trucks),
                "max_iterations": result.metrics.get(
                    "configured_max_iterations",
                    result.iterations,
                ),
                "objective_number": result.metrics.get("objective_number", 1),
                "algorithm_parameters": result.metrics.get(
                    "algorithm_parameters",
                    {},
                ),
            },
            "created_at": now_iso(),
            "completed_at": now_iso(),
            "result": result,
            "error": None,
        }


normalize_saved_results()


def save_container():
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    result_container.saveToFile(RESULTS_FILE)


def integer_value(payload, name, default, minimum):
    value = int(payload.get(name, default))

    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")

    return value


def float_value(payload, name, default, minimum, maximum=None):
    value = float(payload.get(name, default))

    if value <= minimum:
        raise ValueError(f"{name} must be greater than {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must not exceed {maximum}")

    return value


def parse_experiment_config(payload):
    algorithm = payload.get("algorithm")

    if algorithm not in ALGORITHMS:
        raise ValueError("unknown algorithm")

    config = {
        "algorithm": algorithm,
        "experiment_name": payload.get("experiment_name", "").strip() or None,
        "package_count": integer_value(payload, "package_count", 30, 1),
        "truck_count": integer_value(payload, "truck_count", 1, 1),
        "max_iterations": integer_value(payload, "max_iterations", 1000, 1),
        "seed": integer_value(payload, "seed", 42, 0),
        "objective_number": 1,
        "algorithm_parameters": {},
    }

    if algorithm == "Hill Climbing - Sideways Move":
        config["algorithm_parameters"] = {
            "max_sideways": integer_value(payload, "max_sideways", 100, 0),
        }
    elif algorithm == "Hill Climbing - Random Restart":
        config["algorithm_parameters"] = {
            "max_restarts": integer_value(payload, "max_restarts", 5, 0),
        }
    elif algorithm == "Simulated Annealing":
        initial_temperature = float_value(
            payload,
            "initial_temperature",
            100.0,
            0,
        )
        minimum_temperature = float_value(
            payload,
            "minimum_temperature",
            0.01,
            0,
        )

        if minimum_temperature >= initial_temperature:
            raise ValueError(
                "minimum_temperature must be lower than initial_temperature"
            )

        config["algorithm_parameters"] = {
            "initial_temperature": initial_temperature,
            "cooling_rate": float_value(
                payload,
                "cooling_rate",
                0.99,
                0,
                1,
            ),
            "minimum_temperature": minimum_temperature,
        }
    elif algorithm == "Genetic Algorithm":
        config["algorithm_parameters"] = {
            "population_size": integer_value(payload, "population_size", 20, 2),
        }

    return config


def run_experiment_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return

        config = dict(job["config"])

    try:
        problem, initial_state = prepare_initial_state(
            config["package_count"],
            config["seed"],
            config["truck_count"],
        )
        result = run_algorithm(
            config["algorithm"],
            problem,
            initial_state,
            max_iterations=config["max_iterations"],
            seed=config["seed"],
            algorithm_parameters=config["algorithm_parameters"],
            objective_number=config["objective_number"],
            experiment_name=config["experiment_name"],
        )

        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["completed_at"] = now_iso()
                jobs[job_id]["result"] = result
    except Exception as error:
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["completed_at"] = now_iso()
                jobs[job_id]["error"] = str(error)


def serialize_job(job, include_details=False):
    config = job["config"]
    result = job.get("result")
    data = {
        "id": job["id"],
        "status": job["status"],
        "saved": job["saved"],
        "algorithm": config["algorithm"],
        "experiment_name": config["experiment_name"] or "Untitled experiment",
        "seed": config["seed"],
        "package_count": config["package_count"],
        "truck_count": config["truck_count"],
        "max_iterations": config["max_iterations"],
        "algorithm_parameters": json_safe(config["algorithm_parameters"]),
        "created_at": job["created_at"],
        "completed_at": job.get("completed_at"),
        "error": job.get("error"),
        "initial_value": None,
        "final_value": None,
        "best_value": None,
        "iterations": 0,
        "execution_time": None,
        "objective_history": [],
    }

    if result is None:
        return data

    data.update(
        {
            "run_id": result.run_id,
            "run_number": result.run_number,
            "initial_value": result.initial_value,
            "final_value": result.final_value,
            "best_value": result.best_value,
            "iterations": result.iterations,
            "execution_time": result.execution_time,
            "objective_history": json_safe(result.objective_history),
            "termination_reason": result.termination_reason,
            "metrics": json_safe(result.metrics),
        }
    )

    if include_details:
        data.update(
            {
                "initial_state": state_rows(result.problem, result.initial_state),
                "final_state": state_rows(result.problem, result.final_state),
                "best_state": state_rows(result.problem, result.best_state),
            }
        )

    return data


@app.get("/api/algorithms")
def get_algorithms():
    return jsonify(list(ALGORITHMS))


@app.get("/api/experiments")
def get_experiments():
    with jobs_lock:
        ordered_jobs = sorted(
            jobs.values(),
            key=lambda job: job["created_at"],
            reverse=True,
        )
        return jsonify([serialize_job(job) for job in ordered_jobs])


@app.post("/api/experiments")
def create_experiment():
    try:
        config = parse_experiment_config(request.get_json(silent=True) or {})
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400

    job_id = uuid4().hex
    job = {
        "id": job_id,
        "status": "pending",
        "saved": False,
        "config": config,
        "created_at": now_iso(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    with jobs_lock:
        jobs[job_id] = job
        futures[job_id] = executor.submit(run_experiment_job, job_id)

    return jsonify(serialize_job(job)), 202


@app.get("/api/experiments/<job_id>")
def get_experiment(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return jsonify({"error": "experiment not found"}), 404

        return jsonify(serialize_job(job, include_details=True))


@app.post("/api/experiments/<job_id>/save")
def save_experiment(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return jsonify({"error": "experiment not found"}), 404
        if job["status"] != "completed":
            return jsonify({"error": "only completed experiments can be saved"}), 409

        if not job["saved"]:
            result_container.addRes(job["result"])
            save_container()
            job["saved"] = True

        return jsonify(serialize_job(job))


@app.delete("/api/experiments/<job_id>")
def delete_experiment(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return jsonify({"error": "experiment not found"}), 404
        if job["status"] == "pending":
            return jsonify({"error": "a pending experiment cannot be deleted"}), 409

        if job["saved"]:
            result_container.removeRes(job["result"])
            save_container()

        jobs.pop(job_id, None)
        futures.pop(job_id, None)

    return "", 204


@app.get("/api/experiments/<job_id>/export")
def export_experiment(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return jsonify({"error": "experiment not found"}), 404

        response = app.response_class(
            json.dumps(serialize_job(job, include_details=True), indent=2),
            mimetype="application/json",
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="experiment-{job_id}.json"'
        )
        return response


@app.get("/")
def serve_index():
    index_file = FRONTEND_DIST / "index.html"

    if index_file.exists():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return (
        "React frontend has not been built. Run `npm install` and `npm run build` "
        "inside the frontend directory.",
        503,
    )


@app.get("/<path:file_path>")
def serve_frontend(file_path):
    requested = FRONTEND_DIST / file_path

    if requested.is_file():
        return send_from_directory(FRONTEND_DIST, file_path)

    return serve_index()


@atexit.register
def shutdown_executor():
    executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, threaded=True)
