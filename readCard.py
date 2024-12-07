import cv2
import numpy as np
from paddleocr import PaddleOCR
from datetime import datetime
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


def read(image):
    # cropped_id_card = cv2.resize(image, (500, 300))
    # case cùng hướng  
    # isFrontSide_image = cropped_id_card[4:4+77, 14:14+100]
    # isBackSide_image = cropped_id_card[98:98+56, 53:53+66]
    isFrontSide_image = image[6:6+71, 24:24+90]
        # Tọa độ: (x=53, y=98, w=66, h=56)
    isBackSide_image = image[79:79+50, 44:44+60]
    cv2.imshow("isFrontSide_image",isFrontSide_image)
    cv2.imshow("isBackSide_image",isBackSide_image)
    if isFrontSide(isFrontSide_image):
        print("Mặt Trước")
        cv2.imshow("FrontSide_image",isFrontSide_image)
        x_ID, y_ID, w_ID, h_ID = [179, 98, 185, 33]
        ID_pos = image[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]
        x_date, y_date, w_date, h_date = [273, 155, 113 ,23]
        Date_pos = image[y_date:y_date +h_date, x_date:x_date+w_date]
        cv2.imshow("Date_pos 2",Date_pos)
        cv2.imshow("ID_pos 2",ID_pos)
        Document_number, Date_of_birth, Date_of_expire = readfront(ID_pos, Date_pos)
        return Document_number, Date_of_birth, Date_of_expire
    elif isBackSide(isBackSide_image):
        print("Mặt sau")
        cv2.imshow("BackSide_image",isBackSide_image)
        # Tọa độ: (x=3, y=215, w=497, h=79)
        mrz_pos = image[160:160+85, 7:7+471]
        cv2.imshow("mrz_pos 2",mrz_pos)
        Document_number, Date_of_birth, Date_of_expire = readback(mrz_pos)
        return Document_number, Date_of_birth, Date_of_expire
    else:
        # cropped_id_card = cv2.resize(image, (500, 300))
        image = cv2.rotate(image, cv2.ROTATE_180)
        # case ngược hướng
        # isFrontSide_image = cropped_id_card[28:28+56, 38:38+67]
        # isBackSide_image = cropped_id_card[95:95+45, 55:55+65]

        isFrontSide_image = image[10:10+57, 42:42+73]
        # Tọa độ: (x=53, y=98, w=66, h=56)
        isBackSide_image = image[76:76+52, 98:98+65]
        if isFrontSide(isFrontSide_image):
            print("Mặt Trước")
            cv2.imshow("FrontSide_image",isFrontSide_image)
            x_ID, y_ID, w_ID, h_ID = [197, 97, 177, 33]
            ID_pos = image[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]
            x_date, y_date, w_date, h_date = [289, 151, 98 ,25]
            Date_pos = image[y_date:y_date + h_date, x_date:x_date+w_date]
            cv2.imshow("Date_pos 1",Date_pos)
            Document_number, Date_of_birth, Date_of_expire = readfront(ID_pos, Date_pos)
            return Document_number, Date_of_birth, Date_of_expire
        elif isBackSide(isBackSide_image):
            print("Mặt sau")
            cv2.imshow("BackSide_image",isBackSide_image)
            mrz_pos = image[157:157+84, 7:7+478]
            cv2.imshow("mrz_pos 1",mrz_pos)
            Document_number, Date_of_birth, Date_of_expire = readback(mrz_pos)
            return Document_number, Date_of_birth, Date_of_expire
