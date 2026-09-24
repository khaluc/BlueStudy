"""QwenCloud OpenAI-compatible SSE. Never returns reasoning_content."""
import asyncio
import json
import httpx
from packages.llm.gemma_client import InvalidModelResponse


class CloudFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def cloud_error(status):
    if status in (401, 403):
        return 'cloud_auth_error'
    if status == 429:
        return 'cloud_rate_limit'
    if status == 404:
        return 'cloud_model_unavailable'
    return 'cloud_unavailable'


class QwenClient:
    def __init__(self, http, settings):
        self.http, self.settings = http, settings

    async def chat(self, messages):
        settings = self.settings
        key = settings.dashscope_api_key.get_secret_value()
        if not key:
            raise CloudFailure('missing_api_key')
        parts, finished = [], False
        try:
            async with asyncio.timeout(settings.cloud_timeout_seconds):
                async with self.http.stream('POST', settings.qwen_base_url + '/chat/completions',
                    headers={'Authorization': 'Bearer ' + key}, json={
                        'model': settings.qwen_chat_model, 'messages': messages,
                        'enable_thinking': settings.qwen_enable_thinking, 'stream': True,
                        'max_tokens': settings.qwen_max_tokens,
                    }) as response:
                    if response.status_code != 200:
                        raise CloudFailure(cloud_error(response.status_code))
                    async for line in response.aiter_lines():
                        if not line.startswith('data:'):
                            continue
                        data = line[5:].strip()
                        if data == '[DONE]':
                            break
                        event = json.loads(data)
                        if event.get('error'):
                            raise CloudFailure('cloud_invalid_response')
                        choices = event.get('choices') or []
                        if not choices:
                            continue
                        choice = choices[0]
                        reason = choice.get('finish_reason')
                        if reason and reason != 'stop':
                            raise CloudFailure('cloud_incomplete_response')
                        if reason == 'stop':
                            finished = True
                        content = choice.get('delta', {}).get('content')
                        if content:
                            if not isinstance(content, str):
                                raise ValueError('Invalid content')
                            parts.append(content)
                            if sum(map(len, parts)) > 100000:
                                raise ValueError('Output exceeds bound')
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise CloudFailure('cloud_timeout') from exc
        except httpx.HTTPError as exc:
            raise CloudFailure('cloud_unavailable') from exc
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise CloudFailure('cloud_invalid_response') from exc
        answer = ''.join(parts).strip()
        if not finished or not answer:
            raise CloudFailure('cloud_incomplete_response')
        return answer


class ChatRouter:
    def __init__(self, local, cloud, settings):
        self.local, self.cloud, self.settings = local, cloud, settings

    async def chat(self, messages):
        fallback = None
        if self.settings.chat_provider == 'qwen_cloud':
            try:
                answer = await self.cloud.chat(messages)
                return {'answer': answer, 'model': self.settings.qwen_chat_model,
                        'provider': 'qwen_cloud', 'fallback_reason': None}
            except CloudFailure as exc:
                if not self.settings.local_fallback_enabled:
                    raise
                fallback = exc.code
        answer = await self.local.chat(messages)
        return {'answer': answer, 'model': self.settings.ollama_model,
                'provider': 'ollama', 'fallback_reason': fallback}
