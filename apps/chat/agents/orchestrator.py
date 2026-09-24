from apps.chat.agents.classifier_agent import classify
from apps.chat.agents.teaching_agent import teach
from apps.chat.agents.material_agent import generate


class Orchestrator:
    """Explicit dispatch; the model cannot select arbitrary tools or database actions."""
    def __init__(self, model):
        self.model = model

    def run(self, kind, context):
        if kind == 'generate_bundle':
            return generate(context, self.model)
        if kind == 'classify':
            return classify(context, self.model)
        if kind == 'teach' and context.question.strip():
            return teach(context, self.model)
        raise ValueError('Unsupported action or missing question')
