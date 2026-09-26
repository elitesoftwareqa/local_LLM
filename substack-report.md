# Laguna-S 2.1 on a Mac Studio vs. DGX Spark: Same Model, Different Bottlenecks

*A reproducible three-run comparison of oMLX on Apple silicon and vLLM on NVIDIA GB10 hardware.*

I wanted a cleaner comparison than my earlier different-model test, so I ran the same Laguna-S 2.1 workload on both systems. The Mac Studio used the 4-bit MLX-community `Laguna-S-2.1-oQ4e` checkpoint through oMLX. The DGX Spark endpoint used Laguna-S 2.1 in NVIDIA NVFP4 through vLLM.

The result is not a simple winner: the Mac was dramatically faster at token generation, while the DGX was dramatically faster at ingesting a large prompt.

## Results

All figures are medians from three uncached streaming requests. The client ran on the Mac; DGX measurements include local-network and API overhead.

| Metric | Mac Studio M3 Ultra / oMLX | DGX Spark / vLLM |
|---|---:|---:|
| Short-prompt end-to-end, 384 output tokens | **60.97 tok/s** | 20.92 tok/s |
| Short-prompt time to first token | **0.400 s** | 2.644 s |
| Short-prompt decode | **60.97 tok/s** | 24.45 tok/s |
| Long-prompt prefill, 28,433 tokens | 671 tok/s | **1,788 tok/s** |
| Long-prompt decode, 128 output tokens | **51.61 tok/s** | 9.51 tok/s |
| Long-prompt end-to-end | 2.85 tok/s | **4.30 tok/s** |

The short-prompt end-to-end rate is completion tokens divided by full request time. Decode excludes time to first token. Prefill is prompt tokens divided by time to first generated content, so it is an application-level throughput figure rather than a kernel-only measurement.

## The systems

The Mac is an M3 Ultra Mac Studio with 28 CPU cores, a 60-core GPU, 96GB of unified memory, and 819GB/s of memory bandwidth. It ran oMLX with one model loaded and one concurrent request. The checkpoint occupies roughly 60GB on disk and reports a 118B-parameter model with 8B active parameters.

The DGX Spark endpoint ran the same Laguna family through vLLM using NVIDIA’s NVFP4 format. The systems therefore share model architecture and prompts, but not quantization format, runtime, kernels, or memory-management strategy. This is a systems benchmark, not a claim that one chip is intrinsically a fixed multiple faster.

## Why the Mac wins decoding

For a short prompt, the Mac produced its first token in about four-tenths of a second and then generated nearly 61 tokens per second. The DGX took 2.6 seconds to reach its first token and decoded at about 24 tokens per second.

That is the profile of a machine that feels excellent for interactive conversation: low startup latency and a fast stream once generation begins. The Mac’s unified-memory bandwidth is a good match for repeated autoregressive decode steps.

The long-prompt decode result also favored the Mac, although its rate fell to 51.6 tokens per second after the 28k-token context was loaded. The DGX fell much further, to 9.5 tokens per second in this test.

## Why the DGX wins prefill

On the 28,433-token uncached prompt, the DGX reached its first generated content in 15.9 seconds—about 1,788 prompt tokens per second. The Mac needed 42.4 seconds, or roughly 671 prompt tokens per second.

That advantage matters for document analysis, codebase reviews, long logs, and retrieval-augmented prompts. For this 128-token long-context task, the DGX completed the full request in 29.8 seconds versus 44.9 seconds on the Mac.

## What I would use each system for

I would choose the Mac Studio for private interactive work: chat, coding assistance, and repeated short-to-medium prompts where first-token latency and sustained generation dominate.

I would choose the DGX Spark for workflows dominated by large prompt ingestion. If the task is “read this very large document or repository and then answer briefly,” the DGX’s prefill advantage is more important than its lower decode rate.

The practical lesson is that “tokens per second” is not one number. A serving stack has at least three relevant speeds: time to first token, prefill throughput, and decode throughput.

## Method and limitations

The benchmark used an OpenAI-compatible streaming API, one warm-up request, temperature zero, three measured runs per case, and a unique nonce on every prompt to defeat prefix reuse. The short case requested 384 tokens. The long case used a synthetic 900-record operations log and requested 128 tokens.

This measures latency and single-stream speed, not answer quality, power efficiency, maximum concurrency, or total cost. The DGX result is an endpoint-level result and includes network overhead. Different quantization formats and server implementations remain part of the real deployment being compared.

## Reproduce it

The repository contains the dependency-free benchmark client and raw result files. With either server running:

```bash
python benchmark_openai_stream.py \
  --url http://127.0.0.1:8000 \
  --model Laguna-S-2.1-oQ4e \
  --runs 3 \
  --label "Mac Studio / Laguna / oMLX" \
  --output laguna-results.json
```

For the DGX endpoint, change the URL to `http://spark-3f93.local:8000` and the model name to `laguna-s-2.1`.

*Test date: September 26, 2026. Results are rounded; raw measurements are committed alongside this article.*
