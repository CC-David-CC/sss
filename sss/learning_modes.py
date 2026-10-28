"""Explicit experimental conditions; this metadata does not construct loss masks."""
def validate_mode(mode):
    if type(mode) is not dict or set(mode)!={'answer_mode','supervision','format_policy'}:
        raise ValueError('Explicit answer mode, supervision and format policy required')
    if mode['answer_mode'] not in ('direct','reasoning'):
        raise ValueError('Unknown answer mode')
    if mode['supervision'] not in ('answer_only','reasoning_and_answer'):
        raise ValueError('Unknown supervision mode')
    if mode['format_policy'] not in ('exact','structured'):
        raise ValueError('Unknown format policy')
    if mode['answer_mode']=='direct' and mode['supervision']=='reasoning_and_answer':
        raise ValueError('Direct-answer mode has no reasoning targets')
    return dict(mode)
