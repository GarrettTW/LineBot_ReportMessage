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
        if not reportData.get(groupID): # 如果此群組為新加入，會創立一個新的儲存區
            reportData[groupID]={}
        LineMessage = ''
        receivedmsg = event.message.text
        if '姓名' in receivedmsg and '學號' in receivedmsg and '手機' in receivedmsg:
            try:
                if ( # 檢查資料是否有填，字數注意有換行符
                    len(receivedmsg.split('姓名')[-1].split('學號')[0])<3 and
                    len(receivedmsg.split("學號")[-1].split('手機')[0])<3 and 
                    len(receivedmsg.split('手機')[-1].split('地點')[0])<12 and 
                    len(receivedmsg.split('地點')[-1].split('收假方式')[0])<3
                    ):
                    raise Exception
                # 得到學號
                ID = receivedmsg.split("學號")[-1].split('手機')[0][1:]
                if len(ID)==6:
                    ID = int(ID[-4:])
                elif len(ID)<=4:
                    ID = int(ID)
            except Exception:
                LineMessage = '姓名、學號、手機、地點，其中一項未填。'    
            else:
                reportData[groupID][ID] = receivedmsg
                LineMessage = str(ID)+'號弟兄，回報成功。'

        elif '使用說明' in receivedmsg and len(receivedmsg)==4:
            LineMessage = (
                '收到正確格式\n'
                '----------\n'
                '姓名：\n'
                '學號：\n'
                '手機：\n'
                '地點：\n'
                '收假方式：\n'
                '----------\n'
                '才會正確記錄回報。\n'
                '[格式]\n'
                '正確格式範例。\n'
                '[回報統計]\n'
                '顯示未回報號碼。\n'
                '[輸出回報]\n'
                '貼出所有回報，並清空回報紀錄。'
            )
        elif '回報統計' in receivedmsg and len(receivedmsg)==4:
            try:
                LineMessage = (
                    '完成回報的號碼有:\n'
                    +str([number for number in sorted(reportData[groupID].keys())]).strip('[]')
                )
            except BaseException as err:
                LineMessage = '錯誤原因: '+str(err)
        elif '輸出回報' in receivedmsg and len(receivedmsg)==4:
            try:
                LineMessage = ''
                for data in [reportData[groupID][number] for number in sorted(reportData[groupID].keys())]:
                    LineMessage = LineMessage + data +'\n\n'
            except BaseException as err:
                LineMessage = '錯誤原因: '+str(err)
            else:
                reportData[groupID].clear()

        elif '格式' in receivedmsg and len(receivedmsg)==2:
            LineMessage = '姓名：\n學號：\n手機：\n地點：\n收假方式：'
        
        if LineMessage :
            message = TextSendMessage(text=LineMessage)
            line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    global reportData
    reportData = {}
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
