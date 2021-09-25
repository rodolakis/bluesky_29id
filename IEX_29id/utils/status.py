from epics import caget,caput

def Get_All():
    print("\n")
    print("===========================================================")
    Get_energy(q=None)
    print("-----------------------------------------------------------")
    Get_Mono()
    print("-----------------------------------------------------------")
    Get_Slits()
    print("-----------------------------------------------------------")
    Get_Mirror(1)
    Get_Mirror(2)
    Get_Mirror(3)
    print("-----------------------------------------------------------")
    ARPES=Get_mARPES()[1]
    Kappa=Get_mKappa()[1]
    print("ARPES = ",ARPES)
    print("Kappa = ",Kappa)
    print("===========================================================")

def Get_ARPES():
    print("\n")
    print("===========================================================")
    Get_energy(q=None)
    print("-----------------------------------------------------------")
    Get_Mono()
    print("-----------------------------------------------------------")
    Get_Slits()
    print("-----------------------------------------------------------")
    Get_Mirror(3)
    print("-----------------------------------------------------------")
    ARPES=Get_mARPES()[1]
    print("APRES = ",ARPES)
    print("===========================================================")


    def mprint():
        """ 
        Print motor position in current branch as defined by Check_Branch()
        """
    return Print_Motor()

    def Print_Motor():
        mybranch=CheckBranch()
        if mybranch == "c":
            x=round(caget(ARPES_PVmotor('x')[0]),2)
            y=round(caget(ARPES_PVmotor('y')[0]),2)
            z=round(caget(ARPES_PVmotor('z')[0]),2)
            th=round(caget(ARPES_PVmotor('th')[0]),2)
            chi=round(caget(ARPES_PVmotor('chi')[0]),2)
            phi=round(caget(ARPES_PVmotor('phi')[0]),2)
            return [x,y,z,th,chi,phi]
        #    print "x="+str(x), " y="+str(y)," z="+str(z), " theta="+str(th)
            print("\nx,y,z,th = ["+str(x)+","+str(y)+","+str(z)+","+str(th)+","+str(chi)+","+str(phi)+"]")
        elif mybranch == "d":
            x=round(caget("29idKappa:m2.RBV"),0)
            y=round(caget("29idKappa:m3.RBV"),0)
            z=round(caget("29idKappa:m4.RBV"),0)
            tth= round(caget("29idKappa:m9.RBV"),2)
            kth= round(caget("29idKappa:m8.RBV"),2)
            kap= round(caget("29idKappa:m7.RBV"),2)
            kphi=round(caget("29idKappa:m1.RBV"),2)
            th= round(caget("29idKappa:Euler_ThetaRBV"),3)
            chi= round(caget("29idKappa:Euler_ChiRBV"),3)
            phi=round(caget("29idKappa:Euler_PhiRBV"),3)
            #(th,chi,phi)=KtoE(kth,kap,kphi)
            print("\nx,y,z,tth,th,chi,phi   = ["+str(x)+","+str(y)+","+str(z)+","+str(tth)+","+str(th)+","+str(chi)+","+str(phi)+"]")
            print("x,y,z,tth,kth,kap,kphi = ["+str(x)+","+str(y)+","+str(z)+","+str(tth)+","+str(kth)+","+str(kap)+","+str(kphi)+"]")
            #print "\ntth,th,chi,phi = ["+str(round(tth,1))+","+str(round(th,1))+","+str((round(chi,1)))+","+str((round(phi,1)))+"]"
            pos=[x,y,z,tth,kth,kap,kphi]
            return pos
        #elif mybranch == "e":
        #    print(Get_mRSoXS()[1])