"""One bounded POSIX descriptor read for private owner-installed JSON registries."""
import json
import os
from pathlib import Path
import stat


def read_private_json(path,*,maximum_bytes=16*1024**2):
    if type(maximum_bytes) is not int or not 1<=maximum_bytes<=16*1024**2:
        raise ValueError('Bounded owner configuration byte limit required')
    path=Path(path)
    if not path.is_absolute():raise ValueError('Absolute owner configuration path required')
    path=Path(os.path.abspath(path))
    required=('O_NOFOLLOW','O_DIRECTORY','O_CLOEXEC','O_NONBLOCK')
    if os.name!='posix' or any(not hasattr(os,k)for k in required):
        raise ValueError('Owner configuration requires POSIX no-follow descriptors')
    descriptors=[];chain=[]
    identity=lambda r:(r.st_dev,r.st_ino,r.st_size,r.st_mtime_ns,r.st_ctime_ns,r.st_mode,r.st_nlink,r.st_uid)
    try:
        parent=os.open(path.anchor,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        descriptors.append(parent)
        for name in path.parts[1:-1]:
            child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
            descriptors.append(child);chain.append((parent,name,child));parent=child
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent)
        descriptors.append(fd);before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=os.getuid() or before.st_nlink!=1
                or before.st_mode&0o077 or not 0<before.st_size<=maximum_bytes):
            raise ValueError('Bounded private owned regular configuration required')
        chunks=[];count=0
        while True:
            chunk=os.read(fd,min(65536,maximum_bytes+1-count))
            if not chunk:break
            chunks.append(chunk);count+=len(chunk)
            if count>maximum_bytes:raise ValueError('Owner configuration exceeds byte bound')
        raw=b''.join(chunks);after=os.fstat(fd)
        current=os.stat(path.name,dir_fd=parent,follow_symlinks=False)
        if identity(before)!=identity(after) or identity(after)!=identity(current) or len(raw)!=before.st_size:
            raise ValueError('Owner configuration changed during descriptor read')
        for base,name,child in chain:
            held=os.fstat(child);current=os.stat(name,dir_fd=base,follow_symlinks=False)
            if not stat.S_ISDIR(current.st_mode) or (held.st_dev,held.st_ino)!=(current.st_dev,current.st_ino):
                raise ValueError('Owner configuration ancestor changed')
    except OSError as error:
        raise ValueError('Owner configuration descriptor/ancestor unavailable')from error
    finally:
        for fd in reversed(descriptors):os.close(fd)
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise ValueError('Duplicate owner configuration field')
            value[key]=item
        return value
    def reject(value):raise ValueError('Nonfinite owner configuration value')
    try:
        value=json.loads(raw,object_pairs_hook=pairs,parse_constant=reject)
        json.dumps(value,allow_nan=False)
    except (UnicodeError,RecursionError)as error:
        raise ValueError('Invalid bounded owner configuration JSON')from error
    return path,raw,value
