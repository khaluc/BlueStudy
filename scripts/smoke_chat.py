"""Exercise the running HTTP service; outputs require human quality review."""
import json
from pathlib import Path
import httpx


def main():
    prompts = [
        'Giải thích since và for bằng tiếng Việt, kèm hai ví dụ tiếng Anh. Tối đa 120 từ.',
        'Điền và giải thích ngắn: If I ___ (be) you, I would study earlier.',
        'Đổi sang bị động và giải thích ngắn: They built this school in 2010.',
        'Em được mấy điểm bài kiểm tra hôm qua? Nếu chưa biết thì nói rõ.',
    ]
    results = []
    with httpx.Client(base_url='http://127.0.0.1:8001', timeout=120, trust_env=False) as client:
        client.get('/health/ready').raise_for_status()
        for prompt in prompts:
            response = client.post('/chat', json={'message': prompt})
            response.raise_for_status()
            results.append({'prompt': prompt, **response.json()})
            print(f'Completed {len(results)}/{len(prompts)}', flush=True)
    path = Path('data/benchmarks/chat-smoke.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(path)


if __name__ == '__main__':
    main()
