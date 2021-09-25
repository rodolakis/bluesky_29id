from epics import caget, caput
from time import sleep


def Reset_Mono_Limits():
#    caput("29idmono_GRT_TYPE_SP.ONST", 'MEG_PA')
#    caput("29idmono_GRT_TYPE_SP.TWST", 'HEG_JY')
#    caput("29idmono_GRT_TYPE_SP.THST", 'MEG_JY')
    caput("29idmono:ENERGY_SP.DRVL",200)
    caput("29idmono:ENERGY_SP.LOW",200)
    caput("29idmono:ENERGY_SP.LOLO",200)
    caput("29idmono:ENERGY_SP.LOPR",200)
    print("Mono limits have been reset.")