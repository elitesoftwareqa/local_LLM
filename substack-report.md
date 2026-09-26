# Mac Studio vs. a Two-Node GB10 Cluster: What My Local LLM Benchmark Actually Found

*A 96GB M3 Ultra running a 71B DeepSeek distill model faced a DGX Spark–class cluster running the 284B-parameter DeepSeek-V4-Flash. The answer changed dramatically when the prompt got long.*

On September 26, 2026, I benchmarked two local AI systems that take very different routes to private inference.

On one side was a Mac Studio with an M3 Ultra and 96GB of unified memory, serving a 4-bit DeepSeek-R1-Distill-Llama-70B model through MLX. On the other was a two-node NVIDIA GB10 cluster—one NVIDIA DGX Spark and one Acer Veriton GN100—serving DeepSeek-V4-Flash through vLLM and Ray.

This was deliberately a comparison of the models as I actually deploy them, not a laboratory test that forces identical weights onto both platforms. That makes it more useful as a real-world systems comparison, but it also means the results cannot be attributed to hardware alone.

The short version: the Mac felt more immediate on a short prompt, but the two-node GB10 system generated more than twice as fast and crushed the Mac on a 72,000-character context.

## The headline results

| Test | Mac Studio, R1 Distill 70B | Two-node GB10, V4 Flash | Practical winner |
|---|---:|---:|---|
| Short-prompt time to first token | **1.05 s** | 2.32 s | Mac, 2.2× quicker |
| Short-prompt generation | 16.11 tok/s | **34.02 tok/s** | GB10, 2.11× faster |
| Short-prompt total time, 384 tokens | 24.91 s | **13.60 s** | GB10, 1.83× faster |
| Long-prompt time to first token | 206.02 s | **16.14 s** | GB10, 12.76× faster |
| Long-prompt generation | 11.50 tok/s | **35.55 tok/s** | GB10, 3.09× faster |
| Long-prompt total time, 128 tokens | 217.15 s | **19.75 s** | GB10, 10.99× faster |

Every number in the table is the median of three measured runs. Both models were already loaded, one warm-up request was excluded, sampling temperature was zero, and responses streamed through OpenAI-compatible APIs.

## The two systems

### Mac Studio

The Mac was a base M3 Ultra configuration with a 28-core CPU, 60-core GPU, 96GB of unified memory, and 819GB/s of memory bandwidth. Those detected specifications match [Apple’s technical listing for this configuration](https://www.apple.com/shop/product/g1ce9ll/a/Refurbished-Mac-Studio-Apple-M3-Ultra-chip-with-28%E2%80%91Core-CPU-and-60%E2%80%91Core-GPU).

It ran:

- `mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit`
- 71 billion parameters
- 4-bit MLX format, approximately 39.7GB on disk
- MLX-LM 0.31.3 and MLX 0.32.2
- Prompt caching disabled
- A single loaded model on the M3 Ultra

The [MLX model card](https://huggingface.co/mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit) identifies the conversion as a 71B-parameter, 4-bit model and reports a 39.7GB file footprint.

### The GB10 cluster

The second endpoint was not running on one DGX Spark alone. The active Ray cluster contained two GB10 nodes: an NVIDIA DGX Spark and an Acer Veriton GN100. vLLM split the model across both GPUs with tensor parallelism set to two.

Each GB10 has a 20-core Arm CPU and 128GB of coherent unified LPDDR5x memory. NVIDIA specifies 273GB/s of memory bandwidth, up to 1 PFLOP of sparse FP4 tensor performance, and a 140-watt GB10 SoC TDP for a DGX Spark. Full specifications are available on [NVIDIA’s DGX Spark product page](https://www.nvidia.com/en-us/products/workstations/dgx-spark/) and in the [DGX Spark hardware guide](https://docs.nvidia.com/dgx/dgx-spark/hardware.html).

The cluster ran:

- `deepseek-ai/DeepSeek-V4-Flash`
- 284 billion total parameters, with 13 billion activated per token
- Mixed FP4 and FP8 weights
- vLLM 0.25.1 and Ray 2.55.1
- Tensor parallelism across two GB10 GPUs
- FP8 KV cache
- Two-token MTP speculative decoding
- A deployed context cap of 65,536 tokens

DeepSeek’s [official V4-Flash model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) lists 284B total parameters, 13B activated parameters, mixed FP4/FP8 precision, and a theoretical one-million-token model context. My vLLM server was intentionally configured with the smaller 65,536-token ceiling.

## How I tested

I used two tests designed to isolate different parts of the experience.

The first was a short prompt asking for a detailed technical field guide. Each model was allowed to generate 384 tokens. This primarily measured interactive first-token latency and steady single-stream decode speed.

The second was a synthetic operations log containing 900 records, 6,318 whitespace-delimited words, and 71,964 characters. Each model summarized it in up to 128 tokens. Because the tokenizers differ, the identical source text became 21,652 median prompt tokens on the Llama tokenizer and 24,354 on the V4 tokenizer.

I added a unique nonce at the beginning of every measured request. That matters because vLLM can reuse a repeated prompt prefix. Changing the leading prefix forced every long-prompt trial to perform uncached prefill work. The Mac server already had its prompt cache disabled.

The benchmark client ran on the Mac. Its MLX request traveled over loopback, while the GB10 request traveled over the local network. As a result, the network overhead is included in the GB10 figures. This slightly favors the Mac on latency, not the remote system.

## Short prompts: the Mac responds first, then falls behind

For a short prompt, the Mac delivered its first streamed token in 1.05 seconds. The GB10 cluster needed 2.32 seconds. If “feels instant” is the goal, the Mac won that moment.

Once generation began, the outcome reversed. DeepSeek-V4-Flash ran at 34.02 output tokens per second, while the 70B model on the Mac produced 16.11. The GB10 system was 2.11 times faster at sustained decoding and completed the 384-token response in 13.60 seconds instead of 24.91.

That produces an interesting user experience: the Mac begins talking sooner, but the cluster finishes substantially sooner.

## Long prompts: this is where the systems separate

The long-context test was not close.

The Mac took 206.02 seconds—nearly three and a half minutes—to emit its first token. The GB10 cluster took 16.14 seconds. End to end, the Mac required 217.15 seconds, while the cluster finished in 19.75 seconds.

The GB10 deployment therefore cut total latency by roughly 91% and finished the task almost 11 times sooner.

Long context also reduced the Mac’s decode speed from 16.11 to 11.50 tokens per second. The V4 deployment remained near its short-context rate, moving from 34.02 to 35.55 tokens per second in the median runs. The two tokenizers and outputs are not identical, so the small increase should not be interpreted as a universal scaling claim. The important observation is that the GB10 system retained its overall generation rate while the Mac slowed materially.

## Why the result is bigger than “NVIDIA versus Apple”

It would be tempting to call this a pure chip shootout. It is not.

The Mac ran a 71B-parameter Llama-derived model in a 4-bit MLX format. The GB10 cluster ran a much larger mixture-of-experts model, but only 13B of its 284B parameters activate for each token. The deployments also used different inference engines, quantization schemes, KV-cache formats, tokenizers, attention architectures, and speculative decoding settings. Finally, the V4 model was distributed across two computers.

Those differences are not experimental noise; they are the point of this particular comparison. They show what each complete stack delivered in a working local setup. They do not prove that one chip is intrinsically a certain multiple faster than the other.

The shape of the result still makes technical sense. Autoregressive decoding often leans heavily on memory movement, an area where the M3 Ultra’s high unified-memory bandwidth makes a 39.7GB dense model surprisingly capable. Prompt ingestion is more compute-intensive, and V4-Flash was designed around efficient long-context processing. The GB10 deployment also benefits from Blackwell tensor cores, a sparse mixture-of-experts architecture, two GPUs, vLLM, FP8 KV cache, and speculative decoding.

## What I would choose

For interactive chats with modest prompts, the Mac remains compelling. It is quiet, simple, fast to first token, and runs a serious 70B-class model entirely inside one familiar desktop.

For document analysis, repository-scale prompts, large logs, or any workflow where long-context waiting dominates, the two-node GB10 deployment is in a different class. Waiting 16 seconds is noticeable. Waiting 206 seconds changes how willing I am to use the tool at all.

For sustained generation, the cluster also wins clearly: roughly 34 tokens per second versus 16 on short context, and 36 versus 11.5 after a long prompt.

My conclusion is not that the Mac lost. It is that the workload determines which advantage matters. The M3 Ultra offered the better short-prompt first impression. The V4-on-GB10 stack delivered the better finish—and an overwhelming long-context result.

## Caveats

- This benchmark measures speed and latency, not answer quality.
- The systems ran different models and software stacks.
- The GB10 result used two nodes, not a single DGX Spark.
- Prompt token counts differ because the models use different tokenizers.
- The test measured one streaming request at a time, not multi-user throughput.
- Power draw and energy per token were not measured.
- Results describe these exact server settings and software versions; tuning either stack could change them.

## Reproducibility

The benchmark used an OpenAI-compatible streaming client, a warm-up request followed by three measured runs per case, temperature zero, and median aggregation. A unique leading nonce defeated prefix reuse on every measured prompt. The complete script and raw JSON results accompany this article.

*Test date: September 26, 2026. Values are rounded from the raw measurements.*
