"""Pin Python rendering code actually used by an installed optional adapter."""
from pathlib import Path


def rendering_sources(components,*callbacks):
    values=[*callbacks,*components.values()]
    tokenizer=components.get('tokenizer')
    if tokenizer is not None:
        values.extend(getattr(tokenizer,name,None)for name in ('encode','decode'))
    paths=set()
    for value in values:
        target=getattr(value,'__func__',value)
        code=getattr(target,'__code__',None)
        if code is not None:
            paths.add(Path(code.co_filename).resolve(strict=True))
    return sorted(paths)
