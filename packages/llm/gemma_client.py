"""Ollama adapter: no model download and no implicit cloud fallback."""
import httpx


class ModelUnavailable(Exception):
    pass


class ModelTimeout(Exception):
    pass


class InvalidModelResponse(Exception):
    pass


class GemmaClient:
    def __init__(self, http: httpx.AsyncClient, model: str, num_ctx: int = 4096,
                 num_predict: int = 512):
        self.http = http
        self.model = model
        self.num_ctx = num_ctx
        self.num_predict = num_predict

    async def ready(self) -> bool:
        try:
            response = await self.http.get('/api/tags', timeout=5)
            response.raise_for_status()
            return any(item.get('name') == self.model
                       for item in response.json()['models'])
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
            return False

    async def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            response = await self.http.post('/api/chat', json={
                'model': self.model, 'messages': messages, 'stream': False,
                'think': False,
                'options': {'num_ctx': self.num_ctx,
                            'num_predict': self.num_predict},
            })
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelTimeout('Mô hình phản hồi quá thời gian cho phép.') from exc
        except httpx.HTTPError as exc:
            raise ModelUnavailable('Không kết nối được mô hình hoặc mô hình chưa sẵn sàng.') from exc
        try:
            body = response.json()
            content = body['message']['content']
            if body.get('done') is not True or not isinstance(content, str) or not content.strip():
                raise ValueError('Empty or incomplete response')
            if body.get('done_reason') == 'length':
                raise ValueError('Truncated response')
            return content.strip()
        except (ValueError, KeyError, TypeError) as exc:
            raise InvalidModelResponse('Mô hình trả kết quả rỗng, bị cắt hoặc không hợp lệ.') from exc
