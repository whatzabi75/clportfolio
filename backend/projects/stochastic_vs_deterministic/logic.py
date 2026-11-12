"""Ground-truth answers, prompts and scoring for the prompt-consistency demo.

The Anthropic API no longer accepts `temperature`, so randomness can't be dialed
down. Instead the demo asks the same question several times with a loose prompt
and with a strict, grounded prompt, and measures how close (and how consistent)
the answers are, using cosine similarity of MiniLM sentence embeddings.
"""
from itertools import combinations

from sentence_transformers import SentenceTransformer, util

from shared.llm import client, ANTHROPIC_MODEL

model = SentenceTransformer("all-MiniLM-L6-v2")

RUNS_PER_PROMPT = 5
MAX_TOKENS = 400
TOPIC_MATCH_THRESHOLD = 0.50

GROUND_TRUTHS = {
    "What is Meeting Digest?": (
        "Meeting Digests is a feature within Salesforce Meetings that enhances sales reps' "
        "interactions with prospects and customers by providing a unified view of meeting information. "
        "It helps sales reps prepare for meetings by gathering and sharing insights about attendees, "
        "meeting details, and related activities on a single page."
    ),

    "How can I use Meeting Digest?": (
        "To start using Meeting Digest, here are some steps:\n"
        "1. Enable Salesforce Meetings: Ensure that Meeting Digest is enabled.\n"
        "2. Assign Permissions: Reassign users to the permission set.\n"
        "3. Utilize Einstein Activity Capture: Implement an activity sync.\n"
        "4. Prepare for Meetings: Use the Meeting Digest to gather and share information before meetings.\n"
        "5. Take Action on Attendee Details: Update attendee details, start emails, or add new records."
    ),

    "How can Meeting Digest drive value?": (
        "Here are some ways it can add value:\n\n"
        "1. Unified Information: Meeting Digest unifies all relevant information about meeting attendees.\n"
        "2. Enhanced Engagement: The Meeting Studio feature within Meeting Digest allows reps to keep attendees engaged during virtual meetings.\n"
        "3. Actionable Insights: Meeting Digest provides insights into high-priority cases and outstanding customer requests.\n"
        "4. Streamlined Follow-Up: After the meeting, Meeting Digest offers reminders and quick actions for follow-up tasks.\n"
        "5. Improved Collaboration: With the ability to update attendee details directly from the Meeting Digest, sales reps can stay focused on meeting preparation and execution."
    )
}


def loose_system_prompt():
    return "You are a helpful assistant."


def strict_system_prompt(reference):
    rules = (
        "You are a support assistant for Salesforce Meeting Digest.\n"
        "Rules:\n"
        "- Answer only from the reference answer below. Do not add facts, examples or opinions.\n"
        "- Keep its structure: if it is a numbered list, answer with the same numbered list.\n"
        "- Stay close to its wording. No greeting, no preamble, no closing remarks.\n"
    )
    if reference:
        return rules + "\n<reference_answer>\n" + reference + "\n</reference_answer>"
    return rules + "- There is no reference answer for this question: reply in one sentence that you can only help with Meeting Digest."


def find_ground_truth(question):
    """Return (topic, ground_truth) for the closest known question, or (None, None)."""
    question_emb = model.encode(question, convert_to_tensor=True)
    best_topic, best_score = None, 0.0
    for topic in GROUND_TRUTHS:
        score = float(util.cos_sim(question_emb, model.encode(topic, convert_to_tensor=True)))
        if score > best_score:
            best_topic, best_score = topic, score
    if best_score > TOPIC_MATCH_THRESHOLD:
        return best_topic, GROUND_TRUTHS[best_topic]
    return None, None


def generate_answer(system_prompt, question):
    completion = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )
    return "".join(b.text for b in completion.content if b.type == "text").strip()


def _pct(x):
    return round(float(x) * 100, 1)


def summarize_runs(answers, expected_answer):
    """Score each answer against the ground truth, plus how alike the answers are to each other."""
    embs = model.encode(answers, convert_to_tensor=True)
    truth_emb = model.encode(expected_answer, convert_to_tensor=True) if expected_answer else None
    runs = []
    for answer, emb in zip(answers, embs):
        match = _pct(util.cos_sim(truth_emb, emb)[0][0]) if truth_emb is not None else None
        runs.append({"response": answer, "similarity": match})

    pair_scores = [float(util.cos_sim(embs[i], embs[j])[0][0])
                   for i, j in combinations(range(len(answers)), 2)]
    matches = [r["similarity"] for r in runs if r["similarity"] is not None]
    return {
        "runs": runs,
        "avg_similarity": round(sum(matches) / len(matches), 1) if matches else None,
        "min_similarity": min(matches) if matches else None,
        "max_similarity": max(matches) if matches else None,
        # Average similarity between every pair of answers: 100% = identical every time.
        "consistency": _pct(sum(pair_scores) / len(pair_scores)) if pair_scores else None,
    }
