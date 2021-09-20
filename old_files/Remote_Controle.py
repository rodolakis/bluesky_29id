from epics import *

##############################################################################################################
##############################             RSXS Remote control        ##############################
##############################################################################################################

# To start ioc for ARPES(RSXS) Surly(Sneezy)
# cd /net/s29dserv/xorApps/epics/synApps_5_8/ioc/29idSurlySoft/iocboot/iocLinux
# 29idSurlySoft start

# to bring up epics screen
# cd /net/s29dserv/xorApps/epics/synApps_5_8/ioc/29idSurlySoft/
# start_epics_29idSurlySoft

def ARPES_Controller():
    """
    Button={} with Button[][0]=PV name and Button[][1]=value (for tweaks or other procs value=1)
    ".TWF -> (+)tweak"
    ".TWR -> (-)tweak"
    """
    Controller="29idSurlySoft"
    ioc="29idc:"

    Triggers={}    #['LTSeq','RTSeq','LBSeq','RBSeq']
    Triggers[0]=ioc+"allstop.VAL",1
    Triggers[1]=ioc+"allstop.VAL",1
    Triggers[2]=ioc+"allstop.VAL",1
    Triggers[3]=ioc+"allstop.VAL",1

    DPad={}        #['UpSeq','DownSeq','LeftSeq','RightSeq']
    DPad[0]=ioc+"m1.TWF",1            #x
    DPad[1]=ioc+"m1.TWR",1
    DPad[2]=ioc+"m4.TWR",1            #th
    DPad[3]=ioc+"m4.TWF",1

    Buttons={}    #['YSeq','ASeq','XSeq','BSeq']
    Buttons[0]=ioc+"m3.TWF",1        #z
    Buttons[1]=ioc+"m3.TWR",1
    Buttons[2]=ioc+"m2.TWR",1        #y
    Buttons[3]=ioc+"m2.TWF",1

    Ljoy={}        #['LSUpSeq','LSDownSeq','LSLeftSeq','LSRightSeq']
    Ljoy[0]="",0
    Ljoy[1]="",0
    Ljoy[2]=ioc+"m6.TWR",1            #phi
    Ljoy[3]=ioc+"m6.TWF",1            #phi
    Lclick={}    #['L3Seq']
    Lclick[0]=ioc+"m1.TWV",.25        #x
    Lclick[1]=ioc+"m2.TWV",.25        #y
    Lclick[2]=ioc+"m3.TWV",.25        #z
    Lclick[3]=ioc+"m4.TWV",1        #th
    Lclick[4]=ioc+"m5.TWV",1        #chi
    Lclick[5]=ioc+"m6.TWV",1        #phi
    Lclick[6]="",0
    Lclick[7]="",0
    Lclick[8]="",0

    Rjoy={}        #['RSUpSeq','RSDownSeq','RSLeftSeq','RSRightSeq']
    Rjoy[0]="",0
    Rjoy[1]="",0
    Rjoy[2]=ioc+"m5.TWR",1            #chi
    Rjoy[3]=ioc+"m5.TWF",1            #chi
    Rclick={}    #['R3Seq']
    Rclick[0]=ioc+"m1.TWV",.5        #x
    Rclick[1]=ioc+"m2.TWV",.5        #y
    Rclick[2]=ioc+"m3.TWV",.5        #z
    Rclick[3]=ioc+"m4.TWV",5        #th
    Rclick[4]=ioc+"m5.TWV",5        #chi
    Rclick[5]=ioc+"m6.TWV",5        #phi
    Rclick[6]="",0
    Rclick[7]="",0
    Rclick[8]="",0

    Controller_setup(Controller,Triggers,DPad,Buttons,Ljoy,Lclick,Rjoy,Rclick)


def RSXS_Kappa_Controller_backup(): #Keep JM modified below when kth broke
    """
    Button={} with Button[][0]=PV name and Button[][1]=value (for tweaks or other procs value=1)
    ".TWF -> (+)tweak"
    ".TWR -> (-)tweak"
    """
    Controller="29idSneezySoft"
    ioc="29idKappa:"

    Triggers={}    #['LTSeq','RTSeq','LBSeq','RBSeq']
    Triggers[0]=ioc+"m9.TWR",1        #tth
    Triggers[1]=ioc+"m9.TWF",1
    Triggers[2]=ioc+"allstop.VAL",1
    Triggers[3]=ioc+"allstop.VAL",1

    DPad={}        #['UpSeq','DownSeq','LeftSeq','RightSeq']
    DPad[0]=ioc+"m4.TWF",1            #z
    DPad[1]=ioc+"m4.TWR",1
    DPad[2]=ioc+"m1.TWR",1            #phi
    DPad[3]=ioc+"m1.TWF",1

    Buttons={}    #['YSeq','ASeq','XSeq','BSeq']
    Buttons[0]=ioc+"m3.TWF",1        #y
    Buttons[1]=ioc+"m3.TWR",1
    Buttons[2]=ioc+"m2.TWR",1        #x
    Buttons[3]=ioc+"m2.TWF",1

    Ljoy={}        #['LSUpSeq','LSDownSeq','LSLeftSeq','LSRightSeq']
    Ljoy[0]="",0
    Ljoy[1]="",0
    Ljoy[2]=ioc+"m8.TWR",1            #th
    Ljoy[3]=ioc+"m8.TWF",1
    Lclick={}    #['L3Seq']
    Lclick[0]=ioc+"m2.TWV",50        #x
    Lclick[1]=ioc+"m3.TWV",50        #y
    Lclick[2]=ioc+"m4.TWV",50        #z
    Lclick[3]=ioc+"m1.TWV",0.5        #phi (0.5 deg)
    Lclick[4]=ioc+"m7.TWV",0.5        #kappa
    Lclick[5]=ioc+"m8.TWV",0.5        #th
    Lclick[6]=ioc+"m9.TWV",0.5        #tth
    Lclick[7]="",0
    Lclick[8]="",0

    Rjoy={}        #['RSUpSeq','RSDownSeq','RSLeftSeq','RSRightSeq']
    Rjoy[0]="",0
    Rjoy[1]="",0
    Rjoy[2]=ioc+"m7.TWR",1            #kappa
    Rjoy[3]=ioc+"m7.TWF",1
    Rclick={}    #['R3Seq']
    Rclick[0]=ioc+"m2.TWV",250        #x
    Rclick[1]=ioc+"m3.TWV",250        #y
    Rclick[2]=ioc+"m4.TWV",250        #z
    Rclick[3]=ioc+"m1.TWV",5        #phi (45 deg)
    Rclick[4]=ioc+"m7.TWV",5        #kappa
    Rclick[5]=ioc+"m8.TWV",5        #th
    Rclick[6]=ioc+"m9.TWV",5        #tth
    Rclick[7]="",0
    Rclick[8]="",0

    Controller_setup(Controller,Triggers,DPad,Buttons,Ljoy,Lclick,Rjoy,Rclick)

def RSXS_Kappa_Controller():
    """
    Button={} with Button[][0]=PV name and Button[][1]=value (for tweaks or other procs value=1)
    ".TWF -> (+)tweak"
    ".TWR -> (-)tweak"
    """
    Controller="29idSneezySoft"
    ioc="29idKappa:"

    Triggers={}    #['LTSeq','RTSeq','LBSeq','RBSeq']
    Triggers[0]=ioc+"m9.TWR",1        #tth
    Triggers[1]=ioc+"m9.TWF",1
    Triggers[2]=ioc+"allstop.VAL",1
    Triggers[3]=ioc+"allstop.VAL",1

    DPad={}        #['UpSeq','DownSeq','LeftSeq','RightSeq']
    DPad[0]=ioc+"m4.TWF",1            #z
    DPad[1]=ioc+"m4.TWR",1
    DPad[2]=ioc+"m1.TWR",1            #phi
    DPad[3]=ioc+"m1.TWF",1

    Buttons={}    #['YSeq','ASeq','XSeq','BSeq']
    Buttons[0]=ioc+"m3.TWF",1        #y
    Buttons[1]=ioc+"m3.TWR",1
    Buttons[2]=ioc+"m2.TWR",1        #x
    Buttons[3]=ioc+"m2.TWF",1

    Ljoy={}        #['LSUpSeq','LSDownSeq','LSLeftSeq','LSRightSeq']
    Ljoy[0]="29idd:Unidig1Bo0",0        #light on
    Ljoy[1]="29idd:Unidig1Bo0",1        #light off
    Ljoy[2]=ioc+"",0            #th
    Ljoy[3]=ioc+"",0
    Lclick={}    #['L3Seq']
    Lclick[0]=ioc+"m2.TWV",250        #x
    Lclick[1]=ioc+"m3.TWV",250        #y
    Lclick[2]=ioc+"m4.TWV",250        #z
    Lclick[3]=ioc+"m1.TWV",0.5        #phi (0.5 deg)
    Lclick[4]=ioc+"m7.TWV",0.5        #kappa
    Lclick[5]=ioc+"m8.TWV",0.5        #th
    Lclick[6]=ioc+"m9.TWV",0.5        #tth
    Lclick[7]="",0
    Lclick[8]="",0

    Rjoy={}        #['RSUpSeq','RSDownSeq','RSLeftSeq','RSRightSeq']
    Rjoy[0]="",0
    Rjoy[1]="",0
    Rjoy[2]=ioc+"",0            #kappa
    Rjoy[3]=ioc+"",0
    Rclick={}    #['R3Seq']
    Rclick[0]=ioc+"m2.TWV",500        #x
    Rclick[1]=ioc+"m3.TWV",500        #y
    Rclick[2]=ioc+"m4.TWV",500        #z
    Rclick[3]=ioc+"m1.TWV",5        #phi (45 deg)
    Rclick[4]=ioc+"m7.TWV",5        #kappa
    Rclick[5]=ioc+"m8.TWV",5        #th
    Rclick[6]=ioc+"m9.TWV",5        #tth
    Rclick[7]="",0
    Rclick[8]="",0

    Controller_setup(Controller,Triggers,DPad,Buttons,Ljoy,Lclick,Rjoy,Rclick)


def RSoXS_Controller():
    """
    Button={} with Button[][0]=PV name and Button[][1]=value (for tweaks or other procs value=1)
    ".TWF -> (+)tweak"
    ".TWR -> (-)tweak"
    """
    Controller="29idSneezySoft"
    ioc="29idRSoXS:"

    Triggers={}    #['LTSeq','RTSeq','LBSeq','RBSeq']
    Triggers[0]=ioc+"allstop.VAL",1
    Triggers[1]=ioc+"allstop.VAL",1
    Triggers[2]=ioc+"allstop.VAL",1
    Triggers[3]=ioc+"allstop.VAL",1

    DPad={}        #D-Pad:['UpSeq','DownSeq','LeftSeq','RightSeq']
    DPad[0]=ioc+"m10.TWF",1            #Det-V
    DPad[1]=ioc+"m10.TWR",1
    DPad[2]=ioc+"m11.TWR",1            #Det-Q
    DPad[3]=ioc+"m11.TWF",1

    Buttons={}    #Buttons:['YSeq','ASeq','XSeq','BSeq']
    Buttons[0]=ioc+"m2.TWF",1        #y
    Buttons[1]=ioc+"m2.TWR",1
    Buttons[2]=ioc+"m1.TWR",1        #x
    Buttons[3]=ioc+"m1.TWF",1

    Ljoy={}        #Left Joystick:['LSUpSeq','LSDownSeq','LSLeftSeq','LSRightSeq']
    Ljoy[0]=ioc+"m5.TWF",1            #phi
    Ljoy[1]=ioc+"m5.TWR",1
    Ljoy[2]=ioc+"m9.TWR",1            #tth
    Ljoy[3]=ioc+"m9.TWF",1
    Lclick={}    #['L3Seq']
    Lclick[0]="",0
    Lclick[1]="",0
    Lclick[2]="",0
    Lclick[3]="",0
    Lclick[4]="",0
    Lclick[5]="",0
    Lclick[6]="",0
    Lclick[7]="",0
    Lclick[8]="",0

    Rjoy={}        #Right Joystick:['RSUpSeq','RSDownSeq','RSLeftSeq','RSRightSeq']
    Rjoy[0]=ioc+"m3.TWF",1            #z
    Rjoy[1]=ioc+"m3.TWF",1
    Rjoy[2]=ioc+"m8.TWR",1            #th
    Rjoy[3]=ioc+"m8.TWF",1
    Rclick={}    #['R3Seq']
    Rclick[0]=ioc+"m2.TWV",1        #x
    Rclick[1]=ioc+"m3.TWV",1        #y
    Rclick[2]=ioc+"m4.TWV",1        #z
    Rclick[3]=ioc+"m1.TWV",1        #th
    Rclick[4]=ioc+"m7.TWV",1        #phi
    Rclick[5]=ioc+"m8.TWV",1        #tth
    Rclick[6]=ioc+"m9.TWV",1        #Det-V
    Rclick[7]=ioc+"m9.TWV",1        #Det-Q
    Rclick[8]="",0

    Controller_setup(Controller,Triggers,DPad,Buttons,Ljoy,Lclick,Rjoy,Rclick)

def Controller_setup(Controller,Triggers,DPad,Buttons,Ljoy,Lclick,Rjoy,Rclick):
    """ -------- Standard set up for the Logitech controllers --------------
    Controller -> controller ioc name

    Button={}
    Button[][0]=PV name
    Button[][1]=value (for tweaks or other procs value=1)
    ".TWF -> (+)tweak"
    ".TWR -> (-)tweak"

        Trigger[0,3]     -> PVs for link 1 of the 4 buttons (bottoms are typically the allstop)
        DPad[0,3]     -> PVs for link 1 of the 4 buttons (order: Top/Bottom/Left/Right)
        Buttons[0,3]     -> PVs for link 1 of the 4 buttons (order: Top/Bottom/Left/Right)
        Ljoy[0,3]     -> PVs for link 1 of the 4 buttons (order: Top/Bottom/Left/Right)
        Lclick[0,8]    -> PVs for Link 1-9 of the center click (typically coarse tweak values)
        RJoy[0,3]     -> PVs for link 1 of the 4 buttons (order: Top/Bottom/Left/Right)
        Rclick[0,8]    -> PVs for Link 1-9 of the center click (typically fine tweak values)
    """

    #Triggers
    Ctrl_button(Controller,"LTSeq",1,Triggers[0][0],Triggers[0][1])
    Ctrl_button(Controller,"RTSeq",1,Triggers[1][0],Triggers[1][1])
    Ctrl_button(Controller,"LBSeq",1,Triggers[2][0],Triggers[2][1])#All Stop
    Ctrl_button(Controller,"RBSeq",1,Triggers[3][0],Triggers[3][1])#All Stop

    # D-Pad
    Ctrl_button(Controller,"UpSeq",1,   DPad[0][0],DPad[0][1])
    Ctrl_button(Controller,"DownSeq",1, DPad[1][0],DPad[1][1])
    Ctrl_button(Controller,"LeftSeq",1, DPad[2][0],DPad[2][1])
    Ctrl_button(Controller,"RightSeq",1,DPad[3][0],DPad[3][1])


    #Buttons
    Ctrl_button(Controller,"YSeq",1,Buttons[0][0],Buttons[0][1])
    Ctrl_button(Controller,"ASeq",1,Buttons[1][0],Buttons[1][1])
    Ctrl_button(Controller,"XSeq",1,Buttons[2][0],Buttons[2][1])
    Ctrl_button(Controller,"BSeq",1,Buttons[3][0],Buttons[3][1])


    #Left Joystick
    Ctrl_button(Controller,"LSUpSeq",1,   Ljoy[0][0],Ljoy[0][1])
    Ctrl_button(Controller,"LSDownSeq",1, Ljoy[1][0],Ljoy[1][1])
    Ctrl_button(Controller,"LSLeftSeq",1, Ljoy[2][0],Ljoy[2][1])
    Ctrl_button(Controller,"LSRightSeq",1,Ljoy[3][0],Ljoy[3][1])
    #Left Click                    Coarse Tweak Values
    Ctrl_button(Controller,"L3Seq",1,Lclick[0][0],Lclick[0][1])
    Ctrl_button(Controller,"L3Seq",2,Lclick[1][0],Lclick[1][1])
    Ctrl_button(Controller,"L3Seq",3,Lclick[2][0],Lclick[2][1])
    Ctrl_button(Controller,"L3Seq",4,Lclick[3][0],Lclick[3][1])
    Ctrl_button(Controller,"L3Seq",5,Lclick[4][0],Lclick[4][1])
    Ctrl_button(Controller,"L3Seq",6,Lclick[5][0],Lclick[5][1])
    Ctrl_button(Controller,"L3Seq",7,Lclick[6][0],Lclick[6][1])
    Ctrl_button(Controller,"L3Seq",8,Lclick[7][0],Lclick[7][1])
    Ctrl_button(Controller,"L3Seq",9,Lclick[8][0],Lclick[8][1])

    #Right Joystick
    Ctrl_button(Controller,"RSUpSeq",1,   Rjoy[0][0],Rjoy[0][1])
    Ctrl_button(Controller,"RSDownSeq",1, Rjoy[1][0],Rjoy[1][1])
    Ctrl_button(Controller,"RSLeftSeq",1, Rjoy[2][0],Rjoy[2][1])
    Ctrl_button(Controller,"RSRightSeq",1,Rjoy[3][0],Rjoy[3][1])
    #Right Click                    Fine Tweak Values
    Ctrl_button(Controller,"R3Seq",1,Rclick[0][0],Rclick[0][1])
    Ctrl_button(Controller,"R3Seq",2,Rclick[1][0],Rclick[1][1])
    Ctrl_button(Controller,"R3Seq",3,Rclick[2][0],Rclick[2][1])
    Ctrl_button(Controller,"R3Seq",4,Rclick[3][0],Rclick[3][1])
    Ctrl_button(Controller,"R3Seq",5,Rclick[4][0],Rclick[4][1])
    Ctrl_button(Controller,"R3Seq",6,Rclick[5][0],Rclick[5][1])
    Ctrl_button(Controller,"R3Seq",7,Rclick[6][0],Rclick[6][1])
    Ctrl_button(Controller,"R3Seq",8,Rclick[7][0],Rclick[7][1])
    Ctrl_button(Controller,"R3Seq",9,Rclick[8][0],Rclick[8][1])


def Ctrl_reset(Controller):
    PV=""
    val=0
    CtrlButtonList  = ['LTSeq','RTSeq','LBSeq','RBSeq','UpSeq','DownSeq','LeftSeq','RightSeq','YSeq','ASeq','XSeq','BSeq']
    CtrlButtonList.extend(['LSUpSeq','LSDownSeq','LSLeftSeq','LSRightSeq','L3Seq','RSUpSeq','RSDownSeq','RSLeftSeq','RSRightSeq','R3Seq'])
    for button in CtrlButtonList:
        for link in range(1,10):
            Ctrl_but(Controller,button,link,PV,val)

def Ctrl_button(Controller,button,link,PV,val):#writes to specified link (controller has 1 to 9)
    ctlpv=Controller+":ctl1:"+button
    caput(ctlpv+".LNK"+str(link),PV+" NPP NMS")
    caput(ctlpv+".DO"+str(link),val)

def Ctrl_print(Controller):
    CtrlButtonList  = ['LTSeq','RTSeq','LBSeq','RBSeq','UpSeq','DownSeq','LeftSeq','RightSeq','YSeq','ASeq','XSeq','BSeq']
    CtrlButtonList.extend(['LSUpSeq','LSDownSeq','LSLeftSeq','LSRightSeq','L3Seq','RSUpSeq','RSDownSeq','RSLeftSeq','RSRightSeq','R3Seq'])
    for button in CtrlButtonList:
        print("---"+button+"---")
        for link in range(1,10):
            ctlpv=Controller+":ctl1:"+button
            PV=caget(ctlpv+".LNK"+str(link))
            val=caget(ctlpv+".DO"+str(link))
            print("     "+PV+", "+str(val))
