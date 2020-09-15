#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from absl import app
from absl import flags

import src as scf


def main(argv):
    if flag_values.debug:
        flag_values.loglv = 0
    cf:Union[scf.SingleCurveFit, scf.MultipleCurveFit] = scf.CurveFitFactory.get_instance(
        qdp_list=flag_values.qdp, log_file=flag_values.log, plot_flag=flag_values.show, loglv=flag_values.loglv)
    cf.fit()


def define_flags():
    flag_values = flags.FLAGS
    flags.DEFINE_list(
        'qdp', None, 'Path to qdp file(s). If multiple files, input comma-separated list of strings.')
    flags.DEFINE_string(
        'log', 'xisscfcurvefit_result.log', 'Logging file name of fitting result.')
    flags.DEFINE_boolean(
        'show', True, 'Show result plot.', short_name='s')
    flags.DEFINE_boolean(
        'debug', False, 'run with debug mode.')
    flags.DEFINE_enum(
        'loglv', 'INFO',
        ['DEBUG', 'debug', 'INFO', 'info', 'WARNING', 'warning', 'ERROR', 'error'],
        'Logging level.')
    flags.mark_flags_as_required(['qdp'])
    return flag_values


if __name__ == '__main__':
    flag_values = define_flags()
    sys.exit(app.run(main))
