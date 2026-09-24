"""Measure full response latency, not time to first token. Run from project root."""
import argparse
import asyncio
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from apps.chat.config import Settings
from packages.llm.gemma_client import GemmaClient
from packages.llm.prompts import system_prompt


async def benchmark(runs: int):
    settings = Settings()
    async with httpx.AsyncClient(base_url=settings.ollama_base_url,
                                timeout=settings.llm_timeout_seconds, trust_env=False) as http:
        llm = GemmaClient(http, settings.ollama_model, settings.llm_num_ctx,
                          settings.llm_num_predict)
        if not await llm.ready():
            raise SystemExit('Ollama chưa sẵn sàng hoặc chưa tải model: ' + settings.ollama_model)
        version = (await http.get('/api/version')).json()
        tags = (await http.get('/api/tags')).json()
        model_info = next(item for item in tags['models'] if item['name'] == settings.ollama_model)
        samples = []
        for index in range(runs):
            started = time.perf_counter()
            answer = await llm.chat([
                {'role': 'system', 'content': system_prompt()},
                {'role': 'user', 'content': 'Giải thích bằng tiếng Việt sự khác nhau giữa since và for, kèm 2 ví dụ tiếng Anh.'},
            ])
            samples.append({'seconds': round(time.perf_counter() - started, 3),
                            'answer': answer, 'cold_candidate': index == 0})
            print(f'Completed {index + 1}/{runs}', flush=True)
        runtime_memory = (await http.get('/api/ps')).json()
    warm = sorted(sample['seconds'] for sample in samples[1:])
    report = {'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'ollama_version': version, 'model_info': model_info,
              'runtime_memory_after': runtime_memory,
              'model': settings.ollama_model, 'num_ctx': settings.llm_num_ctx,
              'num_predict': settings.llm_num_predict, 'concurrency': 1,
              'measurement': 'full_response_not_first_token',
              'warm_p95_seconds': warm[math.ceil(.95 * len(warm)) - 1] if warm else None,
              'quality_review': 'pending', 'samples': samples}
    path = Path('data/benchmarks/llm.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=6)
    args = parser.parse_args()
    if not 2 <= args.runs <= 100:
        parser.error('--runs must be between 2 and 100')
    asyncio.run(benchmark(args.runs))
