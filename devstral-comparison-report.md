# Devstral Small 2 OptiQ: Mac Studio vs. MacBook Pro

Test date: September 27, 2026. Three uncached streaming runs per case.

## Results

| Metric | Mac Studio M3 Ultra / oMLX | MacBook Pro M5 Pro / MLX server |
|---|---:|---:|
| Short end-to-end, 384 output tokens | **35.52 tok/s** | 16.50 tok/s |
| Short time to first token | 1.376 s | **1.067 s** |
| Short decode | **40.71 tok/s** | 17.30 tok/s |
| Long-prompt prefill | 324.5 tok/s | **456.7 tok/s** |
| Long-context decode | **28.81 tok/s** | 12.55 tok/s |
| Long end-to-end | **1.42 tok/s** | 1.80 tok/s |

The long test used approximately 28k uncached prompt tokens and requested 128 output tokens. Prefill is prompt tokens divided by time to first generated content. End-to-end is completion tokens divided by total request time.

## Interpretation

The Mac Studio is the stronger Devstral generation machine: it decodes about 2.35x faster on the short test and about 2.30x faster after a long prompt. The MacBook reaches its first token sooner and pre-fills large prompts about 1.41x faster, but its lower decode rate makes it slower overall for generated answers.

The Mac Studio used `mlx-community/Devstral-Small-2-24B-Instruct-2512-OptiQ-4bit` through oMLX. The MacBook used the same OptiQ checkpoint from a local path through an MLX-based server. Both used temperature zero, one measured request at a time, and the same benchmark prompts. The MacBook server retained its existing settings: 4,096 maximum output tokens, decode concurrency 8, prompt concurrency 1, prompt cache size 0, 2,048 prefill step size, and thinking disabled. The Mac Studio used oMLX with prompt cache disabled and balanced memory guard.

These are deployment results, not a pure chip-only test: runtimes, scheduling, prefill step size, and memory management differ.
