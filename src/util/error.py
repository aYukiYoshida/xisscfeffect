# -*- coding: utf-8 -*-

class MissingInputError(Exception):
    """入力が不足していることを知らせる例外クラス"""
    pass

class InvalidInputError(Exception):
    """入力が相応しくないことを知らせる例外クラス"""
    pass