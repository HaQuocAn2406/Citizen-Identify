import cv2
import numpy as np
from paddleocr import PaddleOCR
from datetime import datetime
ocr_model = PaddleOCR(lang='en')


def isFrontSide(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    # lower_red2 = np.array([160, 70, 100])
    # upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    # mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    mask = mask1
    if np.any(mask):
        return True
    else:
        return False


def isBackSide(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([15, 100, 100])
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
    for item in mrz:  # Truy cập vào danh sách con đầu tiên
        for sub_item in item:  # Truy cập vào từng phần tử trong danh sách con
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
    if Date[0][0][1][0] is not None:
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
        print("Trường Hợp 25t")
        DayOfExpire = DayOfBirth
        MonthOfExpire = MonthOfBirth
        YearOfExpire = str(25+int(YearOfBirth))
    elif 23 <= age < 38:
        print("Trường Hợp 40t")
        DayOfExpire = DayOfBirth
        MonthOfExpire = MonthOfBirth
        YearOfExpire = str(40+int(YearOfBirth))
    elif 38 <= age < 58:
        print("Trường Hợp 60t")
        DayOfExpire = DayOfBirth
        MonthOfExpire = MonthOfBirth
        YearOfExpire = str(60+int(YearOfBirth))
    else:
        print("Trường Hợp Vô Thời Hạn")
        DayOfExpire = '31'
        MonthOfExpire = '12'
        YearOfExpire = "99"
    Date_of_expire = YearOfExpire+MonthOfExpire+DayOfExpire
    print(f"Date ={Date}")
    print(f"Expire = {DayOfExpire}/{MonthOfExpire}/{str(YearOfExpire)}")
    return Document_number, Date_of_birth, Date_of_expire


def readCard(image):
    cropped_id_card = cv2.resize(image, (500, 300))
    # case cùng hướng
    isFrontSide_image = cropped_id_card[49:49+83, 34:34+132]
    isBackSide_image = cropped_id_card[115:115+81, 59:59+106]
    if isFrontSide(isFrontSide_image):
        print("Mặt Trước")
        x_ID, y_ID, w_ID, h_ID = [215, 135, 178, 48]
        x_date, y_date, w_date, h_date = [307, 193, 98, 27]
        ID_pos = cropped_id_card[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]
        Date_pos = cropped_id_card[y_date:y_date + h_date, x_date:x_date+w_date]
        readfront(ID_pos, Date_pos)
    elif isBackSide(isBackSide_image):
        print("Mặt sau")
        mrz_pos = cropped_id_card[197:197+92, 35:35+463]
        readback(mrz_pos)
    else:
        cropped_id_card = cv2.resize(image, (500, 300))
        cropped_id_card = cv2.rotate(cropped_id_card, cv2.ROTATE_180)
        # case cùng hướng
        isFrontSide_image = cropped_id_card[11:11+85, 2:2+111]
        isBackSide_image = cropped_id_card[78:78+79, 18:18+101]
        if isFrontSide(isFrontSide_image):
            print("Mặt Trước")
            x_ID, y_ID, w_ID, h_ID = [168, 102, 177, 38]
            x_date, y_date, w_date, h_date = [258, 156, 101, 28]
            ID_pos = cropped_id_card[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]
            Date_pos = cropped_id_card[y_date:y_date + h_date, x_date:x_date+w_date]
            readfront(ID_pos, Date_pos)
        elif isBackSide(isBackSide_image):
            print("Mặt sau")
            mrz_pos = cropped_id_card[163:163+85, 6:6+447]
            readback(mrz_pos)
