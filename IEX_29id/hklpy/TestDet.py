from epics import *
import numpy as np
import time
import datetime

from ScanFunctions_IEX import setdet



class testgain:
    def __init__(self):
        self._srs = None
        self.value = None
        self.unit = None

class testname:
    def __init__(self):
        self.d3 = None
        self.d4 = None
        self.mcp = None
        self.tey = None
        self.mesh = None



class det:

    def __init__(self):
        self.current = caget('29idKappa:userStringSeq6.STR1')
        self.d3 = None
        self.d4 = None
        self.mcp = None
        self.tey = None
        self.mesh = None