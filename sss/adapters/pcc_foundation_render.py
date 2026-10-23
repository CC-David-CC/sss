"""Exact PCC chat rendering for owned direct-answer foundation practice."""
import hashlib
from sss.adapters.foundation_training import SYSTEM
from sss.records import digest


class PCCFoundationRenderer:
    def __init__(self, components):
        self.encoder = components['render'].__self__
        self.tokenizer = components['tokenizer']
        self.renderer_sha256 = digest(dict(template_sha256=hashlib.sha256(
            self.encoder.template.source.encode()).hexdigest(), thinking=False,
            source_sha256=hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),
            system=SYSTEM))

    def __call__(self, exercise, answer):
        from serve.server import Service
        # These exact generator inputs contain no literal model-control text.
        # Reject such input instead of misencoding it with parse_special=True.
        specials = set(getattr(self.tokenizer, 'special_tokens', ()))
        if any(token and token in text for token in specials for text in (exercise.prompt, answer, SYSTEM)):
            raise ValueError('Literal model control text needs a different qualified renderer')
        messages = [dict(role='system', content=SYSTEM), dict(role='user', content=exercise.prompt)]
        kwargs = dict(enable_thinking=False, add_generation_prompt=True)
        prefix = self.encoder.render_prompt(messages, None, kwargs)
        completed_messages = messages + [dict(role='assistant', content=answer)]
        complete = self.encoder.render_prompt(completed_messages, None,
            dict(enable_thinking=False, add_generation_prompt=False))
        if not complete.startswith(prefix) or len(complete) <= len(prefix):
            raise ValueError('Completed chat does not extend its actual inference prefix')
        prefix_ids = Service.encode_prompt(self.encoder, messages, None, kwargs)
        full_ids = Service.encode_prompt(self.encoder, completed_messages, None,
            dict(enable_thinking=False, add_generation_prompt=False))
        if (full_ids[:len(prefix_ids)] != prefix_ids
                or self.tokenizer.encode(prefix, parse_special=True) != prefix_ids
                or self.tokenizer.encode(complete, parse_special=True) != full_ids):
            raise ValueError('Training tokens differ from the actual serving renderer')
        # The user span includes the unselected assistant generation header.
        # Selected labels are only the checked answer and its template terminator.
        return [dict(role='user', kind='question', rendered=prefix, verified=False, scope='practice'),
                dict(role='assistant', kind='answer', rendered=complete[len(prefix):],
                     verified=True, scope='practice')]
