# Devstral Small 2 on an M3 Ultra Mac Studio vs. an M5 Pro MacBook Pro

*The same coding model reveals two different Apple-silicon strengths: the MacBook reads prompts faster, while the Mac Studio writes answers much faster.*

I benchmarked the same Devstral Small 2 24B OptiQ checkpoint on two Apple computers:

- Mac Studio with M3 Ultra, 96GB unified memory, served by oMLX
- MacBook Pro with M5 Pro, 48GB memory, served by an MLX-based server

Both systems used the same model weights, the same prompts, temperature zero, and three uncached streaming runs per case.

## The results

- Short-prompt end-to-end speed:
  - Mac Studio: **35.52 tokens per second**
  - MacBook Pro: 16.50 tokens per second

- Short-prompt decode speed:
  - Mac Studio: **40.71 tokens per second**
  - MacBook Pro: 17.30 tokens per second

- Short-prompt time to first token:
  - Mac Studio: 1.376 seconds
  - MacBook Pro: **1.067 seconds**

- Long-prompt prefill speed:
  - Mac Studio: 324.5 tokens per second
  - MacBook Pro: **456.7 tokens per second**

- Long-context decode speed:
  - Mac Studio: **28.81 tokens per second**
  - MacBook Pro: 12.55 tokens per second

- Long-context end-to-end speed:
  - Mac Studio: **1.42 tokens per second**
  - MacBook Pro: 1.80 tokens per second

The long test used roughly 28,000 uncached prompt tokens and generated 128 output tokens.

## What the numbers mean

The MacBook Pro was better at prefill. It processed a large prompt approximately 41% faster than the Mac Studio and reached the first token slightly sooner.

The Mac Studio was much better at decode. Once generation began, it produced more than twice as many tokens per second. For coding conversations and long answers, that difference dominates the experience.

This produces an interesting tradeoff. The MacBook can begin sooner, but the Mac Studio streams the answer much faster and usually finishes a substantial response sooner.

## Which one would I choose?

I would choose the Mac Studio for:

- Interactive coding
- Long generated answers
- Repeated conversations
- Higher sustained output speed
- Running larger local models

I would choose the MacBook Pro for:

- Portable local inference
- Large prompts followed by short answers
- Lower first-token latency
- Prompt-heavy workflows where reading context dominates

The broader lesson is that local LLM performance has at least two important phases. Prefill measures how quickly the system reads the prompt. Decode measures how quickly it writes the answer. The MacBook’s newer processor was strong at the first phase; the Mac Studio’s larger GPU and memory system were much stronger at the second.

## Caveats

This was a deployment comparison, not a perfectly controlled hardware experiment. The Mac Studio used oMLX, while the MacBook used a custom MLX-based server with different concurrency and prefill settings. Both used the same OptiQ checkpoint and benchmark prompts, but runtime behavior still affects the result.

The benchmark measured speed, not answer quality, power consumption, energy per token, or multi-user throughput.

*Test date: September 27, 2026. Raw JSON results and the benchmark client are available in the accompanying GitHub repository.*
