from __future__ import unicode_literals

import datetime
import errno
import json
import os
import sys
import tempfile
from argparse import ArgumentParser
from dotenv import load_dotenv

from flask import Flask, request, abort, send_from_directory,make_response
from werkzeug.middleware.proxy_fix import ProxyFix

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, PostbackEvent, StickerMessage, StickerSendMessage, 
    LocationMessage, LocationSendMessage, ImageMessage, ImageSendMessage)

import time
from pathlib import Path

import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, non_max_suppression, apply_classifier, scale_coords, xyxy2xywh, \
    strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized
import pickle 
import wikipedia
import pyrebase
import datetime
import wolframalpha
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

# reads the key-value pair from .env file and adds them to environment variable.
load_dotenv()

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None or channel_access_token is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
    
#===== Firebase ====================================================
config = {
    'apiKey': "AIzaSyCl-wWBByv3261Uu_h5IBqp15fV5iMaGzI",
    'authDomain': "ai-detection-5a2b6.firebaseapp.com",
    'databaseURL': "https://ai-detection-5a2b6-default-rtdb.firebaseio.com",
    'projectId': "ai-detection-5a2b6",
    'storageBucket': "ai-detection-5a2b6.appspot.com",
    'messagingSenderId': "865732945786",
    'appId': "1:865732945786:web:e671ea10f3ecff9c82d8c3",
    'measurementId': "G-4FJ30SDMPG",
  };


firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

user = auth.sign_in_with_email_and_password("kevinangas@gmail.com", "Mikey131998")



storage = firebase.storage()
 

def add_image_db(img_path):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    path_on_cloud = f"images/{timestamp}.jpg"
    path_local = img_path
    storage.child(path_on_cloud).put(path_local)



### YOLOv5 ###
# Setup
def delete_all(): 
    try: 
        for i in os.listdir("static"): 
            os.remove(i)
    except: 
        pass

# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

@app.route("/", methods=['GET'])
def home():

    return "<marquee behavior='scroll' direction='left' scrollamount=15>Food Recognition AI</marquee>"



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
    except LineBotApiError as e:
 
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
   
     
    except InvalidSignatureError:
        abort(400)

    return 'OK'



@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    #เรียกใช้ฟังก์ชัน generate_answer เพื่อแยกส่วนของคำถาม
    text = event.message.text
    if text.lower() == "1": 
            weights = "yolov5s.pt"
            with open("model.pkl","wb") as f: 
                f.write(pickle.dumps(weights))
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text="เปลี่ยนเป็นโหมดตรวจจับวัตถุ"),
                ]
            )       
    elif text.lower() == "2": 
            weights = "best.pt"
            with open("model.pkl","wb") as f: 
                f.write(pickle.dumps(weights))
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text="เปลี่ยนเป็นโหมดตรวจจับอาหารไทย"),
                ]
            )           
    elif text.lower() == "3":
            weights = "best_BCCM.pt"
            with open("model.pkl","wb") as f: 
                f.write(pickle.dumps(weights))
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text="เปลี่ยนเป็นโหมดตรวจจับเม็ดเลือด"),
                ]
            )     

    elif "คำนวณ" in text.lower():
        try:

            client = wolframalpha.Client("G84Y4Q-6K6GVKXLRA")
           
        
            response = client.query(text[text.index("คำนวณ")+len("คำนวณ "):])
            
            result = None
            for result in response.results:
                pass
            # You could have also simply used result = list(response.results)[-1]
            
            if result is not None:
                ans_real = f"คำตอบของคุณ คือ {result.text}".format(result.text)
                
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=ans_real))
        except:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="ไม่เข้าใจเลยค่ะ พูดใหม่ได้ไหม"))  
    
    
    elif text.lower() == "เปลี่ยนเป็นภาษาอังกฤษ" or text.lower() == "english" or text.lower() == "eng" or text.lower() == "อังกฤษ" or text.lower() == "ค้นหาด้วยาษาอังกฤษ":
        wikipedia.set_lang('en')
        line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="ค้นหา wikipedia ด้วยภาษาอังกฤษ"))
    elif text.lower() == "เปลี่ยนเป็นภาษาไทย" or text.lower() == "thai" or text.lower() == "th" or text.lower() == "ไทย" or text.lower() == "ค้นหาด้วยาษาไทย":
        wikipedia.set_lang('th')
        line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="ค้นหา wikipedia ด้วยภาษาไทย"))
    elif text.lower() == "delete" or text.lower() == "ลบภาพ" or text.lower() == "ลบ":
        for i in os.listdir(static_tmp_path): 
            os.remove(os.path.join(static_tmp_path,i))
        line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="ลบภาพทั้งหมด เรียบร้อยแล้วค่ะ"))
    elif "ค้นหา" in text.lower():
        try:
            ans = wikipedia.summary(text[text.index("ค้นหา")+len("ค้นหา"):])
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=ans))
        except:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="ไม่เข้าใจเลยค่ะ พูดใหม่ได้ไหม"))
    elif "search" in text.lower(): 
        text = text.lower()
   
        try:
            
            ans = wikipedia.summary(text[text.index("search")+len("search"):])
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=ans))

        except:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="ไม่เข้าใจเลยค่ะ พูดใหม่ได้ไหม"))
    
    elif text.lower() == "close" or text.lower() == "ปิด" or text.lower() == "ปิดโหมดตรวจจับวัตถุ": 
          line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text="ปิดโหมดตรวจจับวัตถุในภาพแล้วค่ะ"))      
    else: 
        pass
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title='Location', address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )




# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage))
def handle_content_message(event):
    #============== Set Up Yolo============================
    
    with open('model.pkl','rb') as f: 
        
        a = pickle.loads(f.read())
        
    weights, view_img, save_txt, imgsz = a, False, False, 640
    
    # weights, view_img, save_txt, imgsz = 'yolov5s.pt', False, False, 640
    conf_thres = 0.25
    iou_thres = 0.45
    classes = None
    agnostic_nms = False
    save_conf = False
    save_img = True
    
    # Directories
    save_dir = 'static/tmp/'
    
    # Initialize
    set_logging()
    device = select_device('')
    half = device.type != 'cpu'  # half precision only supported on CUDA
    
    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    imgsz = check_img_size(imgsz, s=model.stride.max())  # check img_size
    if half:
        model.half()  # to FP16
        
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    else:
        return
    

    
    
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    
    

    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)
    add_image_db(dist_path)
    # Set Dataloader
    dataset = LoadImages(dist_path, img_size=imgsz)
        
    # Get names and colors
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

    # Run inference
    t0 = time.time()
    img = torch.zeros((1, 3, imgsz, imgsz), device=device)  # init img
    _ = model(img.half() if half else img) if device.type != 'cpu' else None  # run once
    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        t1 = time_synchronized()
    
        pred = model(img, augment=False)[0]

        # Apply NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes=classes, agnostic=agnostic_nms)
        t2 = time_synchronized()

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir + p.name)  # img.jpg
            s += '%gx%g ' % img.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f'{n} {names[int(c)]}s, '  # add to string

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format

                    if save_img or view_img:  # Add bbox to image
                        label = f'{names[int(cls)]} {conf:.2f}'
                        plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=3)

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)

            # Print time (inference + NMS)
            print(f'{s}Done. ({t2 - t1:.3f}s)')
            
    url = request.url_root + '/static/tmp/' + dist_name

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text="รายงานผลลัพธ์การตรวจจับวัตถุ "),
            ImageSendMessage(url,url)
        ])

@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)

# create tmp dir for download content
make_static_tmp_dir()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

