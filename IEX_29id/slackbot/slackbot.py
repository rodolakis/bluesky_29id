from epics import *
from ScanFunctions_IEX import *
from ScanFunctions_plot import * 
from slack_bolt import App 
from slack_bolt.adapter.socket_mode import SocketModeHandler 

bot_token = "xoxb-2096024238160-2083899415011-Qu1WBWadTP3fuc9soKoxEINw" 
app_token = "xapp-1-A0228RUP5AA-2076882813270-2219730435a68f81cd068345bca25aebf14da25d8fb196e80dda1670bf010903" 



def text_match(txt_src, txt_tgt): 
    if txt_tgt[:len(txt_src)].lower()==txt_src.lower(): 
        return True 
    else: 
        return False

app = App(token = bot_token) 



@app.event("message") 
def reply(payload, say, client): 
    try: 
        text = payload["text"] 
    except: 
        return 
    user = client.users_info(user=payload["user"])["user"]["real_name"] 
    chan = client.conversations_info(channel=payload["channel"])["channel"]["name"] 
    print(chan, user) 
    if chan == "automated": 
        f_dict={'ring':"S:SRcurrentAI.VAL",
                'permit':"EPS:29:ID:FE:PERM",
                'shutter':'',
                'latest':'',
                'transfer':'',
                'scan':['29idKappa:scan1.SMSG','29idKappa:saveData_fileName','29idKappa:scanProgress:remainingTimeStr','29idKappa:scanProgress:percentDone']
                
               
               }

        if text_match(text,"hello".lower()): 
            say("Greetings *{0}*!".format(user)) 
        if text_match(text,"ring".lower()): 
            SR=caget(f_dict['ring'])
            msg = "Ring current: {:.1f} mA".format(SR)
            say(msg)        
        if text_match(text,"permit".lower()): 
            permit=caget(f_dict['permit'],as_string=True)
            msg = "Beam status: {0}".format(permit)
            say(msg)
        if text_match(text,"shutter".lower()):
            shutter=Get_MainShutter()
            msg = "Shutter Open: {0}".format(shutter)
            say(msg)
        if text_match(text,"scan".lower()): 
            status=caget(f_dict['scan'][0],as_string=True)
            scanNum=caget(f_dict['scan'][1])
            remaining=caget(f_dict['scan'][2])
            percent=caget(f_dict['scan'][3])
            msg0 = "Status: {0}".format(status)
            msg1 = "File: {0}".format(scanNum)
            msg2 = "Progress {:.0f}%".format(percent)
            msg3 = "Remaining: {0}".format(remaining)
            say(msg0)
            say(msg1)
            say(msg2)
            say(msg3)

        if text_match(text, "latest".lower()): 
            path= '/home/beams/29IDUSER/Documents/User_Folders/'+MDA_CurrentUser()+'/lastfigure.png'
            img = path
            image = mpimg.imread(img)
            #plt.figure(figsize=(5,5))
            #plt.imshow(image,cmap='gray',vmin=v1,vmax=v2)
            #plt.imshow(image,cmap='gray')
            #plt.axis('off')
            #plt.savefig("slack_attachment.png", bbox_inches='tight') 
            #plt.close()
            #fig, ax = plt.subplots(1,1) 
            #ax.imshow(img, cmap="gray") 
            #plot_mda(100,34,filepath="/net/s29data/export/data_29idd/2021_1/Comin/mda",prefix='Kappa_')
            #fig.savefig("slack_attachment.png", bbox_inches='tight') 
            #plt.close(fig) 
            #client.files_upload(channels="#automated",file="slack_attachment.png") 
            client.files_upload(channels="#automated",file=img) 
        if text_match(text,"transfer".lower()):
            msg = """Transfer checklist: \n
                     - close beamline valve and shutter
                     - turn off high voltage...."""
            say(msg)


        elif text == 'help'.lower():
            for text in f_dict:
                say(text)




if __name__ == "__main__": 
    SocketModeHandler(app, app_token).start() 

 
