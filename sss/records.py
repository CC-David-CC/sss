"""Content identities shared across optional adapters; no runtime authority."""
import hashlib
import json

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def digest(value):return hashlib.sha256(canonical(value)).hexdigest()

def file_sha256(path):
    with open(path,'rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
