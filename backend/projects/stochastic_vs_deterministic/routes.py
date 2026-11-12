from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, request, jsonify

from .logic import (
    RUNS_PER_PROMPT,
    find_ground_truth,
    generate_answer,
    loose_system_prompt,
    strict_system_prompt,
    summarize_runs,
)

bp = Blueprint("stochastic_vs_deterministic", __name__)


@bp.route("/api/prompt-consistency", methods=["POST"])
def prompt_consistency_demo():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    topic, expected_answer = find_ground_truth(question)
    prompts = {
        "loose": loose_system_prompt(),
        "strict": strict_system_prompt(expected_answer),
    }

    # Ask the same question several times per prompt, all calls in parallel.
    jobs = [(name, system) for name, system in prompts.items() for _ in range(RUNS_PER_PROMPT)]
    try:
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            answers = list(pool.map(lambda job: generate_answer(job[1], question), jobs))
    except Exception as exc:  # surface API problems to the page instead of a bare 500
        return jsonify({"error": f"LLM call failed: {exc}"}), 502

    results = {}
    for name in prompts:
        runs = [answer for (job_name, _), answer in zip(jobs, answers) if job_name == name]
        results[name] = summarize_runs(runs, expected_answer)

    return jsonify({
        "question": question,
        "matched_topic": topic,
        "expected_answer": expected_answer,
        "runs_per_prompt": RUNS_PER_PROMPT,
        "loose": {"system_prompt": prompts["loose"], **results["loose"]},
        "strict": {"system_prompt": prompts["strict"], **results["strict"]},
    })
