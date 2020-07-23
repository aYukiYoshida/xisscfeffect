# -*- coding: utf-8 -*-

from numpy import exp


def energy_event_density_curve(E, Et, C, epsilon):
    return Et*(1 - C*exp(-1*epsilon*E))
