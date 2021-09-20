from epics import PV


def epics_ring(eps_prefix, ioc_prefix, ad_prefix, fp_prefix):

    pvs = {}

    # Ring
    pvs['Current']                  = PV('S:SRcurrentAI')
    pvs['ShutterStatus']            = PV('EPS:29:ID:SS2:POSITION')
    pvs['ShutterPermit']            = PV('EPS:29:ID:FE:PERM')
    pvs['BeamReady']                = PV('ACIS:ShutterPermit')
    
    return pvs


def epics_eps(eps_prefix, ioc_prefix, ad_prefix, fp_prefix):
    """eps_prefix = 29id:BLEPS"""
    pvs = {}

    # EPS
    pvs['BLEPS:B:red']                  = PV(eps_prefix+':ALARM:RED')
    pvs['BLEPS:C:red']                  = PV(eps_prefix+':ARPES:RED')
    pvs['BLEPS:D:red']                  = PV(eps_prefix+':RSXS:RED')
    pvs['BLEPS:B:green']                = PV(eps_prefix+':ALARM:GREEN')
    pvs['BLEPS:C:green']                = PV(eps_prefix+':ARPES:GREEN')
    pvs['BLEPS:D:green']                = PV(eps_prefix+':RSXS:GREEN')
    
    
    return pvs


def epics_id(eps_prefix, ioc_prefix, ad_prefix, fp_prefix):
    """ ioc_prefix = ID29"""
    pvs = {}
    # ID info
    pvs['ID:rbv']         =PV(ioc_prefix+':EnergyRBV')
    pvs['ID:sp']          =PV(ioc_prefix+':EnergySet.VAL')
    pvs['ID:qp:rbv']      =PV(ioc_prefix+':QuasiRatio.RVAL')
    pvs['ID:qp:val']      =PV(ioc_prefix+':QuasiRatioIn.C')
    pvs['ID:mode']        =PV(ioc_prefix+':ActualMode')
    pvs['ID:feedback']    =PV(ioc_prefix+':feedback.VAL')
    pvs['ID:BusyRecord']  =PV(ioc_prefix+':BusyRecord')
    pvs['ID:ModeBusyRec'] =PV(ioc_prefix+':ModeBusyRec')
    return pvs
