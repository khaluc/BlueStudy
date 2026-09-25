import httpx


class ModelTool:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def ask(self, prompt: str, response_language: str = 'vi') -> tuple[str, str]:
        return self._ask(prompt, 'chat', response_language)

    def ask_material(self, prompt: str, response_language: str = 'vi') -> tuple[str, str]:
        return self._ask(prompt, 'study_bundle', response_language)

    def _ask(self, prompt: str, purpose: str, response_language: str = 'vi') -> tuple[str, str]:
        with httpx.Client(base_url=self.base_url, timeout=220, trust_env=False) as client:
            response = client.post('/chat', json={'message': prompt, 'purpose': purpose, 'response_language': response_language})
            response.raise_for_status()
            data = response.json()
        if not isinstance(data.get('answer'), str) or not data['answer'].strip():
            raise ValueError('Invalid answer')
        if not isinstance(data.get('model'), str) or not data['model']:
            raise ValueError('Invalid model name')
        self.last_metadata = {key: data.get(key) for key in ('provider', 'fallback_reason')}
        return data['answer'], data['model']
