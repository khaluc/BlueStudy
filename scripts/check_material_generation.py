"""Diagnose a single synthetic source without logging credentials."""
import json
from pathlib import Path
from pydantic import ValidationError
from apps.chat.agents.material_agent import generate
from apps.chat.tools.model_tool import ModelTool
from packages.core.contracts import AgentContext


class Capture(ModelTool):
    def ask_material(self, prompt):
        answer, name = super().ask_material(prompt)
        path=Path('data/benchmarks/generation-diagnostic.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'answer':answer,'model':name,**self.last_metadata},ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'model':name, **self.last_metadata}))
        return answer,name


if __name__=='__main__':
    try:
        result=generate(AgentContext(document_id='synthetic',language_level='basic',text=
            'In our local community, volunteers help older neighbours. The library lends books for free. '
            'A firefighter puts out fires. A gardener plants trees in the public park. '
            'People take the bus to reduce traffic. Students clean the park every Sunday.'),Capture('http://127.0.0.1:8001'))
        print('Valid grounded study bundle')
    except ValidationError as exc:
        print(json.dumps(exc.errors(include_input=False, include_url=False), default=str))
        raise SystemExit(1)
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(1)
