# Laguna-S 2.1 benchmark

Reproducible comparison of Laguna-S 2.1 on a Mac Studio (oMLX/MLX oQ4e) and DGX Spark (vLLM/NVFP4).

## Run

The client uses only Python’s standard library. Start an OpenAI-compatible server, then run:

```bash
python benchmark_openai_stream.py \
  --url http://127.0.0.1:8000 \
  --model Laguna-S-2.1-oQ4e \
  --runs 3 \
  --label "Mac Studio / Laguna / oMLX" \
  --output laguna-results.json
```

For the DGX Spark, use `--url http://spark-3f93.local:8000` and `--model laguna-s-2.1`.

The script reports prompt tokens, time to first token, total time, generation time, and output tokens/sec for a short-generation case and a 28k-token uncached prompt case. A unique nonce defeats prefix-cache reuse between measured runs.

See [substack-report.md](substack-report.md) for the article and the two `laguna-*-results.json` files for raw measurements.
