# -*- coding: utf-8 -*-

import os
from typing import List

from ..util.object import ObjectLikeDict


def get_file_prefix(name: str) -> str:
    return os.path.splitext(os.path.basename(name))[0]


def file_name_parse(name: str) -> ObjectLikeDict:
    file_prefix = get_file_prefix(name)
    element: List = file_prefix.split('_')
    reference: int = element.index('phase')

    return ObjectLikeDict(
        xis=element[0].replace('x', 'XIS'),
        phase='phase:'+'.'.join(element[reference+1])+'-'+'.'.join(element[reference+2]))
