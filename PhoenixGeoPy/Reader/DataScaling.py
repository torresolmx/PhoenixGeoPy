# -*- coding: utf-8 -*-
"""Class to contain the different data scaling types that can be produced by
a time series reader of the MTU-5C Family
"""

__author__ = 'Jorge Torres-Solis'


class DataScaling:
    AD_in_ADunits, AD_input_volts, instrument_input_volts = range(3)
