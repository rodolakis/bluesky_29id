

from epics import caput


def Move_ARPES_Sample(ListPosition):
    """ListPosition = ["Sample Name", x, y, z, th, chi, phi]"""
    if not isinstance(ListPosition[0],str):
        ListPosition.insert(0,"")
    name,x,y,z,th,chi,phi=ListPosition
    print("\nx="+str(x), " y="+str(y)," z="+str(z), " theta="+str(th)," chi="+str(chi)," phi="+str(phi),"\n")
    Move_ARPES_Motor("x",x)
    Move_ARPES_Motor("y",y)
    Move_ARPES_Motor("z",z)
    Move_ARPES_Motor("th",th)
    Move_ARPES_Motor("chi",chi)
    Move_ARPES_Motor("phi",phi)
    #print "Sample now @:",name




def ARPES_PVmotor(name):
    """
    used to get the PV associated with a given motor(pnuemonic)
    have gotten rid of all hard coding of the motors, use this instead
    usage:
        ARPES_PVmotor('phi') => ['29idc:m6.RBV', '29idc:m6.VAL', '29idc:m6.SPMG','29idc:m6']
    """
    motor={'x': 1,
      'y':2,
      'z':3,
      'th':4,
      'chi':5,
      'phi':6,
      }
    if name in motor:
        m=str(motor[name])
        PV='29idc:m'+m
        m_VAL=PV+'.VAL'
        m_RBV=PV+'.RBV'
        m_SPMG=PV+'.SPMG'
    return [m_RBV,m_VAL,m_SPMG,PV]


def Move_ARPES_Motor(name,val):
    """
    Moves a motor in the ARPES chamber based on common name, not PV name
    name = x,y,z,th,chi,phi
    """
    m_RBV=ARPES_PVmotor(name)[0]
    m_VAL=ARPES_PVmotor(name)[1]
    caput(m_VAL,val,wait=True,timeout=18000)


 