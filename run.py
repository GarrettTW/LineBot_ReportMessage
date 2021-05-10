from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import sys
import os

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('Channel Access Token')
# Channel Secret
handler = WebhookHandler('Channel Secret')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# Added manual format -Garrett, 2021.05.10
def msg_manual_report(user_msg, groupID, userName):
    user_msg = user_msg.replace('自訂回報','').strip()
    ID = str(userName)
    reportData[groupID][ID] = user_msg
    tmp_str = str(ID)+'，回報成功。'  
    return tmp_str      

def msg_report(user_msg, groupID):
    try:
        if ( # 檢查資料是否有填，字數注意有換行符
            len(user_msg.split('姓名')[-1].split('學號')[0])<3 and
            len(user_msg.split("學號")[-1].split('手機')[0])<3 and 
            len(user_msg.split('手機')[-1].split('地點')[0])<12 and 
            len(user_msg.split('地點')[-1].split('收假方式')[0])<3
            ):
            raise Exception
        # 得到學號
        ID = user_msg.split("學號")[-1].split('手機')[0][1:]
        # 直接完整save學號 -Garrett, 2021.01.28  
        ID = str(int(ID)) #先數值再字串，避免換行困擾
        # 學號不再限定只有5碼 -Garrett, 2021.01.28  
        #if len(ID)==6:
        #    ID = int(ID[-4:])
        #elif len(ID)<=4:
        #    ID = int(ID)
    except Exception:
        tmp_str = '姓名、學號、手機、地點，其中一項未填。'       
    else:
        reportData[groupID][ID] = user_msg
        tmp_str = str(ID)+'號弟兄，回報成功。'  
    return tmp_str        
        

def msg_readme():
    tmp_str = (
        '回報格式有兩種方法\n'
        '[1]固定格式。\n'
        '----------\n'
        '姓名：\n'
        '學號：\n'
        '手機：\n'
        '地點：\n'
        '收假方式：\n'
        '----------\n'
        '\n'
        '[2]開頭帶有自訂回報\n'
        '後帶的訊息皆會直接紀錄\n'
        '----------\n'
        '自訂回報\n'
        '王小明範例訊息\n'
        '----------\n'
        '\n'
        '指令\n' 
        '----------\n'   
        '•格式\n'
        '->預設格式範例。\n'
        '•回報統計\n'
        '->顯示完成回報的號碼。\n'
        '•輸出回報\n'
        '->貼出所有回報，並清空回報紀錄。\n'
        '•清空\n'
        '->可手動清空Data，除錯用。\n'
        '----------\n' 
        '效果可參閱此說明\n'
        'https://github.com/GarrettTW/linebot_reportmessage/blob/master/README.md'
    )
    return tmp_str

def msg_cnt(groupID):
    tmp_str = ''
    try:
        tmp_str = (
            '完成回報的號碼有:\n'
            +str([number for number in sorted(reportData[groupID].keys())]).strip('[]')
        )
    except BaseException as err:
        tmp_str = '錯誤原因: '+str(err)
    return tmp_str

def msg_output(groupID):
    try:
        tmp_str = ''
        for data in [reportData[groupID][number] for number in sorted(reportData[groupID].keys())]:
            tmp_str = tmp_str + data +'\n\n'      
    except BaseException as err:
        tmp_str = '錯誤原因: '+str(err)
    else:
        reportData[groupID].clear()
    return tmp_str
def msg_format():
    tmp_str = '姓名：\n學號：\n手機：\n地點：\n收假方式：'
    return tmp_str
    
def msg_clear(groupID):
    reportData[groupID].clear()
    tmp_str = '資料已重置!'
    return tmp_str
    
# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 各群組的資訊互相獨立
    try:
        groupID = event.source.group_id
    except: # 此機器人設計給群組回報，單兵不可直接一對一回報給機器人
        message = TextSendMessage(text='我只接收群組內訊息，請先把我邀請到群組!')
        line_bot_api.reply_message(event.reply_token, message)
    else:
        userID = event.source.user_id

        g_profile = line_bot_api.get_group_summary(groupID)
        groupName = g_profile.group_name

        u_profile = line_bot_api.get_group_member_profile(groupID,userID)
        userName = u_profile.display_name
        userName = str(userName)

        if not reportData.get(groupID): # 如果此群組為新加入，會創立一個新的儲存區
            reportData[groupID]={}
        LineMessage = ''
        receivedmsg = event.message.text

        if '姓名' in receivedmsg and '學號' in receivedmsg and '手機' in receivedmsg:
            LineMessage = msg_report(receivedmsg,groupID)
        elif '自訂回報' in receivedmsg[:4]:
            LineMessage = msg_manual_report(receivedmsg,groupID,userName)
        elif '使用說明' in receivedmsg and len(receivedmsg)==4:
            LineMessage = msg_readme()        
        elif '回報統計' in receivedmsg and len(receivedmsg)==4:
            LineMessage = msg_cnt(groupID)
        elif '格式' in receivedmsg and len(receivedmsg)==2:
            LineMessage = msg_format()
        elif '輸出回報' in receivedmsg and len(receivedmsg)==4:
            LineMessage = msg_output(groupID)
        # for Error Debug, Empty all data -Garrett, 2021.01.27        
        elif '清空' in receivedmsg and len(receivedmsg)==2:
            LineMessage = msg_clear(groupID)
            
        if LineMessage :
            message = TextSendMessage(text=LineMessage)
            line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    global reportData
    reportData = {}
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
