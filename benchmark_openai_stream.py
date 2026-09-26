#!/usr/bin/env python3
"""Small, dependency-free benchmark for OpenAI-compatible chat endpoints."""

import argparse
import json
import statistics
import time
import urllib.request
import uuid


def request_stream(base_url, model, prompt, max_tokens):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    start = time.perf_counter()
    first_token = None
    usage = {}
    text_parts = []
    with urllib.request.urlopen(request, timeout=600) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if chunk.get("usage"):
                usage = chunk["usage"]
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content") or ""
            reasoning = (
                delta.get("reasoning_content")
                or delta.get("reasoning")
                or ""
            )
            emitted = reasoning + content
            if emitted:
                if first_token is None:
                    first_token = time.perf_counter()
                text_parts.append(emitted)
    end = time.perf_counter()
    prompt_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    ttft = (first_token - start) if first_token else None
    generation_time = (end - first_token) if first_token else None
    return {
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "ttft_s": ttft,
        "total_s": end - start,
        "generation_s": generation_time,
        "output_tok_s": (
            output_tokens / generation_time
            if output_tokens and generation_time and generation_time > 0
            else None
        ),
        "characters": sum(len(part) for part in text_parts),
    }


def median(values):
    clean = [value for value in values if value is not None]
    return statistics.median(clean) if clean else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    decode_prompt = (
        "Write a detailed technical field guide to running large language models "
        "locally. Cover memory, quantization, prompt processing, token generation, "
        "concurrency, thermals, and measurement pitfalls. Use numbered sections and "
        "keep writing until you reach the response limit. Do not include a conclusion."
    )
    records = []
    for i in range(900):
        latency = 18 + (i * 17) % 83
        queue = (i * 7) % 19
        records.append(
            f"Request {i:04d}: region=west, latency_ms={latency}, "
            f"queue_depth={queue}, status=ok, cache={'hit' if i % 3 else 'miss'}."
        )
    long_prompt = (
        "The following is a synthetic operations log. Analyze it and provide exactly "
        "five concise bullets describing recurring patterns.\n\n" + "\n".join(records)
    )
    cases = [
        ("decode_384", decode_prompt, 384),
        ("long_prompt_128", long_prompt, 128),
    ]

    # Warm up model execution and the HTTP path; exclude this run from results.
    request_stream(args.url, args.model, "Reply with the word ready.", 8)

    results = []
    for case_name, prompt, max_tokens in cases:
        runs = []
        for run_number in range(1, args.runs + 1):
            # Change the leading prefix on every measured request so server-side
            # prefix caches cannot turn a prefill benchmark into a cache benchmark.
            uncached_prompt = f"Benchmark nonce: {uuid.uuid4()}\n{prompt}"
            result = request_stream(args.url, args.model, uncached_prompt, max_tokens)
            result["run"] = run_number
            runs.append(result)
            print(json.dumps({"case": case_name, **result}), flush=True)
        results.append(
            {
                "name": case_name,
                "max_tokens": max_tokens,
                "runs": runs,
                "median": {
                    "prompt_tokens": median([r["prompt_tokens"] for r in runs]),
                    "output_tokens": median([r["output_tokens"] for r in runs]),
                    "ttft_s": median([r["ttft_s"] for r in runs]),
                    "total_s": median([r["total_s"] for r in runs]),
                    "generation_s": median([r["generation_s"] for r in runs]),
                    "output_tok_s": median([r["output_tok_s"] for r in runs]),
                },
            }
        )

    report = {
        "label": args.label,
        "url": args.url,
        "model": args.model,
        "runs_per_case": args.runs,
        "timestamp_epoch": time.time(),
        "cases": results,
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
