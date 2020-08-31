# -*- coding: utf-8 -*-

import os
import re
from typing import List

from ..util.object import ObjectLikeDict
from ..util.error import InvalidInputError


def get_file_prefix(name: str) -> str:
    return os.path.splitext(os.path.basename(name))[0]

def get_unified_file_prefix(names: List[str]) -> str:
    prefixes = set(
        re.sub('0[1-9]_0[1-9]', 'multi', prefix) for prefix in [
            get_file_prefix(name) for name in names ])
    if len(prefixes) == 1:
        return list(prefixes)[0]
    else:
        raise InvalidInputError('Input qdp files are invalid')

def get_file_property(name: str) -> ObjectLikeDict:
    prefix = get_file_prefix(name)
    element: List = prefix.split('_')
    reference: int = element.index('phase')

    return ObjectLikeDict(
        xis=element[0].replace('x', 'XIS'),
        phase='phase:'+'.'.join(element[reference+1])+'-'+'.'.join(element[reference+2]))

def get_multiple_file_property(names: List[str]) -> ObjectLikeDict:
    unified_prefix = get_unified_file_prefix(names)
    xis = get_file_property(unified_prefix).xis
    phase = [ get_file_property(name).phase for name in names]
    return ObjectLikeDict(xis=xis, phase=phase)
