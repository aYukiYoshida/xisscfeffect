# -*- coding: utf-8 -*-

class ObjectLikeDict(dict):
    def __getattr__(self, name):
        return self.get(name)
