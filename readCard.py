import cv2
import numpy as np
from paddleocr import PaddleOCR
from datetime import datetime
import matplotlib.pyplot as plt
ocr_model = PaddleOCR(lang='en')


def isFrontSide(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([5, 255, 255])
    lower_red2 = np.array([160, 70, 100])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    mask = mask1|mask2
    if np.any(mask):
        return True
    else:
        return False


def isBackSide(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([10, 50, 50])
    upper_yellow = np.array([40, 255, 255])
    mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    if np.any(mask):
        return True
    else:
        return False


def readback(mrz_pos):
    gray_mrz = cv2.cvtColor(mrz_pos, cv2.COLOR_BGR2GRAY)
    mrz = ocr_model.ocr(gray_mrz)
    line = []
    for item in mrz:  # Truy cáº­p vÃ o danh sÃ¡ch con Äáº§u tiÃªn
        for sub_item in item:  # Truy cáº­p vÃ o tá»«ng pháº§n tá»­ trong danh sÃ¡ch con
            coordinates = sub_item[0]
            text, confidence = sub_item[1]
            print(f"MRZ: {text}")
            line.append(str(text).replace('<', ''))
    print(f'Line 1: {line[0]}')
    print(f'Line 2: {line[1]}')
    print(f'Line 3: {line[2]}')
    ID = str(line[0][15:27])
    Document_number = ID[3:]
    Date_of_birth = str(line[1][:6])
    Date_of_expire = str(line[1][8:14])
    return Document_number, Date_of_birth, Date_of_expire


def readfront(ID_pos, Date_pos):
    ID = ocr_model.ocr(ID_pos)
    Date = ocr_model.ocr(Date_pos)
    # if Date[0][0][1][0] is not None:
    ID = str(ID[0][0][1][0])
    Date = str(Date[0][0][1][0]).replace("/", "")
    Document_number = ID[3:]
    now = datetime.now().date().year
    DayOfBirth = Date[:2]
    MonthOfBirth = Date[2:4]
    YearOfBirth = ID[4:6]
    Date_of_birth = YearOfBirth+MonthOfBirth+DayOfBirth
    age = (now - int(YearOfBirth)) % 100
    print(f"Age :{age}")
    if 14 <= age < 23:
        # print("TrÆ°á»ng Há»£p 25t")
        DayOfExpire = DayOfBirth
        MonthOfExpire = MonthOfBirth
        YearOfExpire = str(25+int(YearOfBirth))
    elif 23 <= age < 38:
        # print("TrÆ°á»ng Há»£p 40t")
        DayOfExpire = DayOfBirth
        MonthOfExpire = MonthOfBirth
        YearOfExpire = str(40+int(YearOfBirth))
    elif 38 <= age < 58:
        # print("TrÆ°á»ng Há»£p 60t")
        DayOfExpire = DayOfBirth
        MonthOfExpire = MonthOfBirth
        YearOfExpire = str(60+int(YearOfBirth))
    else:
        # print("TrÆ°á»ng Há»£p VÃ´ Thá»i Háº¡n")
        DayOfExpire = '31'
        MonthOfExpire = '12'
        YearOfExpire = "99"
    Date_of_expire = YearOfExpire+MonthOfExpire+DayOfExpire
    print(f"Date ={Date}")
    print(f"Expire = {DayOfExpire}/{MonthOfExpire}/{str(YearOfExpire)}")
    return Document_number, Date_of_birth, Date_of_expire


def read(image):
    isFrontSide_image = image[6:6+42, 38:38+47]
    isBackSide_image = image[65:65+36, 40:40+48]
    if isFrontSide(isFrontSide_image):
        print("Mặt Trước")
        x_ID, y_ID, w_ID, h_ID = [150, 70, 185, 30]
        ID_pos = image[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]
        x_date, y_date, w_date, h_date = [222, 114, 113 ,23]
        Date_pos = image[y_date:y_date +h_date, x_date:x_date+w_date]
        Document_number, Date_of_birth, Date_of_expire = readfront(ID_pos, Date_pos)
        cv2.rectangle(image,(x_ID,y_ID),(x_ID+w_ID,y_ID+h_ID),(255,0,0),2)
        cv2.rectangle(image,(x_date,y_date),(x_date+w_date,y_date+h_date),(255,0,0),2)  
    elif isBackSide(isBackSide_image):
        print("Mặt sau")
        mrz_pos = image[125:125+65, 0:0+387]
        Document_number, Date_of_birth, Date_of_expire = readback(mrz_pos)
        cv2.rectangle(image,(0,125),(9+387,125+65),(255,0,0),2)
        cv2.rectangle(image,(40,65),(40+48,65+36),(255,0,0),2)
    else:
        image = cv2.rotate(image, cv2.ROTATE_180)
        return read(image) 
    return Document_number, Date_of_birth, Date_of_expire