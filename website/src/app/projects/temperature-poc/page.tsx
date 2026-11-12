"use client";

import { useState } from "react";
import { BACKEND_URL } from "@/lib/backend";
import { motion } from "framer-motion";

interface Run {
  response: string;
  similarity: number | null;
}

interface PromptResult {
  system_prompt: string;
  runs: Run[];
  avg_similarity: number | null;
  min_similarity: number | null;
  max_similarity: number | null;
  consistency: number | null;
}

interface DemoResult {
  question: string;
  matched_topic: string | null;
  expected_answer: string | null;
  runs_per_prompt: number;
  loose: PromptResult;
  strict: PromptResult;
}

const sampleQuestions = [
  "What is Meeting Digest?",
  "How can I use Meeting Digest?",
  "How can Meeting Digest drive value?",
];

const scoreColor = (score: number | null) => {
  if (score === null) return "text-gray-500";
  if (score >= 85) return "text-green-700";
  if (score >= 70) return "text-yellow-700";
  return "text-orange-700";
};

const fmt = (score: number | null) => (score === null ? "–" : `${score.toFixed(1)}%`);

function PromptColumn({
  title,
  subtitle,
  result,
  accent,
}: {
  title: string;
  subtitle: string;
  result: PromptResult;
  accent: string;
}) {
  const [open, setOpen] = useState<number | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  return (
    <div className={`border rounded-2xl p-4 ${accent}`}>
      <h2 className="font-semibold text-gray-800">{title}</h2>
      <p className="text-xs text-gray-600 mb-3">{subtitle}</p>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-white rounded-lg p-2 text-center">
          <p className="text-xs text-gray-500">Avg. match</p>
          <p className={`text-xl font-semibold ${scoreColor(result.avg_similarity)}`}>
            {fmt(result.avg_similarity)}
          </p>
          {result.min_similarity !== null && (
            <p className="text-xs text-gray-500">
              range {fmt(result.min_similarity)} – {fmt(result.max_similarity)}
            </p>
          )}
        </div>
        <div className="bg-white rounded-lg p-2 text-center">
          <p className="text-xs text-gray-500">Consistency</p>
          <p className={`text-xl font-semibold ${scoreColor(result.consistency)}`}>
            {fmt(result.consistency)}
          </p>
          <p className="text-xs text-gray-500">answers vs. each other</p>
        </div>
      </div>

      <div className="space-y-2">
        {result.runs.map((run, idx) => (
          <div key={idx} className="bg-white rounded-lg border border-gray-200">
            <button
              onClick={() => setOpen(open === idx ? null : idx)}
              className="w-full flex justify-between items-center px-3 py-2 text-sm"
            >
              <span className="text-gray-700">
                {open === idx ? "▾" : "▸"} Run {idx + 1}
              </span>
              <span className={`font-semibold ${scoreColor(run.similarity)}`}>
                {run.similarity === null ? "no reference" : fmt(run.similarity)}
              </span>
            </button>
            {open === idx && (
              <p className="px-3 pb-3 text-sm text-gray-800 whitespace-pre-line">{run.response}</p>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={() => setShowPrompt(!showPrompt)}
        className="mt-3 text-xs text-blue-600 hover:underline"
      >
        {showPrompt ? "Hide" : "Show"} system prompt
      </button>
      {showPrompt && (
        <pre className="mt-2 text-xs bg-white border border-gray-200 rounded-lg p-2 whitespace-pre-wrap text-gray-700">
          {result.system_prompt}
        </pre>
      )}
    </div>
  );
}

export default function PromptConsistencyDemo() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<DemoResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${BACKEND_URL}/api/prompt-consistency`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 px-4">
      <div className="max-w-4xl w-full bg-white shadow-md rounded-2xl p-6">
        <h1 className="text-2xl font-semibold text-gray-800 mb-1">
          Stochastic vs. Deterministic Output
        </h1>
        <p className="text-gray-600 mb-3">
          An LLM gives a slightly different answer every time you ask it the same question. For a
          support agent, that is a problem: two customers asking the same thing should get the same
          recommendation.
        </p>
        <p className="text-gray-600 mb-6">
          The randomness can&apos;t simply be switched off (Claude&apos;s API no longer offers a
          temperature setting), so this demo shows the lever that is left: <strong>the prompt</strong>.
          Each click asks your question 5 times with a <em>loose</em> prompt and 5 times with a{" "}
          <em>strict, grounded</em> support prompt, then scores every answer against a ground-truth
          answer using sentence-embedding cosine similarity (all-MiniLM-L6-v2).
        </p>

        <div className="flex flex-wrap gap-2 mb-4">
          {sampleQuestions.map((q) => (
            <button
              key={q}
              onClick={() => setQuestion(q)}
              className="px-3 py-1 bg-blue-50 hover:bg-blue-100 text-blue-600 text-sm rounded-full transition"
            >
              {q}
            </button>
          ))}
        </div>

        <div className="flex gap-2 mb-6">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && handleSubmit()}
            placeholder="Ask a question about Meeting Digest..."
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition disabled:opacity-50"
          >
            {loading ? "Running 10 answers..." : "Run 5× each"}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-6 text-sm">
            {error}
          </div>
        )}

        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            {result.expected_answer ? (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6">
                <p className="text-sm font-semibold text-blue-700">
                  Ground truth for &ldquo;{result.matched_topic}&rdquo;:
                </p>
                <p className="text-blue-800 text-sm mt-1 whitespace-pre-line">{result.expected_answer}</p>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-6 text-sm text-gray-600 italic">
                No ground-truth answer for this question, so only consistency (how alike the 5 answers
                are) is scored. Try one of the sample questions for the full comparison.
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-2">
              <PromptColumn
                title="Loose prompt"
                subtitle="Generic assistant, no reference material"
                result={result.loose}
                accent="bg-orange-50 border-orange-200"
              />
              <PromptColumn
                title="Strict prompt"
                subtitle="Grounded in the reference answer, fixed format"
                result={result.strict}
                accent="bg-green-50 border-green-200"
              />
            </div>

            <p className="text-xs text-gray-500 mt-4">
              Match = cosine similarity between an answer and the ground truth. Consistency = average
              similarity between every pair of the 5 answers (100% = the same answer every time).
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
