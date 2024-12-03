import cv2
from tkinter import *
from tkinter.font import Font
from paddleocr import PaddleOCR
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np
import readData
import os
import face_recognition
import threading
import time
ocr_model = PaddleOCR(lang='en')
root = Tk()

root.title("Xác Thực CCCD")
root.geometry("1200x750")
video_width, video_height = 500, 300
video_label = Label(root, width=video_width, height=video_height)
video_label.place(x=0, y=0)
crop_label = Label(root, width=video_width, height=video_height)
crop_label.place(x=550, y=0)
message_label =Label(root, text="", font=("Arial", 14), fg="red")
message_label.pack()
Face = Label(root, text="Mặt Căn Cước")
Face.place(x=20, y=500)
Facebox = Entry(state=DISABLED, fg='White')
Facebox.place(x=100, y=500)

ID_label = Label(root, text="Mã Căn Cước")
ID_label.place(x=20, y=550)
IDbox = Entry(state=DISABLED, fg='White')
IDbox.place(x=100, y=550)  

Date_label = Label(root, text="Ngày Sinh")
Date_label.place(x=20, y=600)
Datebox = Entry(state=DISABLED, fg='White')
Datebox.place(x=100, y=600)

Expire_label = Label(root, text="Ngày Hết Hạn")
Expire_label.place(x=20, y=650)
Expirebox = Entry(state=DISABLED, fg='White')
Expirebox.place(x=100, y=650)

key = 0

cap = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(2)
copy_image = None


def get_limits(color):
    c = np.uint8([[color]])  # BGR values
    hsvC = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)

    hue = hsvC[0][0][0]  # Get the hue value

    # Handle red hue wrap-around
    if hue >= 165:  # Upper limit for divided red hue
        lowerLimit = np.array([hue - 10, 100, 100], dtype=np.uint8)
        upperLimit = np.array([180, 255, 255], dtype=np.uint8)
    elif hue <= 15:  # Lower limit for divided red hue
        lowerLimit = np.array([0, 100, 100], dtype=np.uint8)
        upperLimit = np.array([hue + 10, 255, 255], dtype=np.uint8)
    else:
        lowerLimit = np.array([hue - 10, 100, 100], dtype=np.uint8)
        upperLimit = np.array([hue + 10, 255, 255], dtype=np.uint8)

    return lowerLimit, upperLimit


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


# red = [0, 0, 255]
# u, p = get_limits(color=red)
# print(u, p)


def update_frame():
    global copy_image
    global face
    ret, frame = cap.read()
    ret, frame2 = cap2.read()
    small_frame = cv2.resize(frame2, (0, 0), fx=0.25, fy=0.25)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
    face_locations = face_recognition.face_locations(rgb_frame)

        # Check number of faces
    if len(face_locations) == 0 or len(face_locations) > 1:
            message_label.config(text="Vui lòng canh chỉnh để DUY NHẤT gương mặt trong khung hình")
    else:
        message_label.config(text="Gương mặt hợp lệ!")
    if ret:
        frame = cv2.resize(frame, (int(video_width), int(video_height)))
        frame2 = cv2.resize(frame2, (int(video_width), int(video_height)))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        # thresh1 = cv2.adaptiveThreshold(blurred,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
        _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.imshow("Binary", thresh1)
        cv2.imshow("Camera 2",frame2)
        if not contours:
            return update_frame()
        biggest = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(biggest)
        box = cv2.boxPoints(rect).astype('int')
        x, y, w, h = cv2.boundingRect(biggest)
        # cv2.drawContours(frame,[box],-1,(0,0,255),2)
        cv2.rectangle(frame, (x+5, y+5), (x + w-5, y + h-5), (255, 0, 0), 2)
        copy_image = frame[y+5:y+h-5, x+5:x+w-5]
        face = frame2
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        imgtk = ImageTk.PhotoImage(image=img)

        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        face = cv2.cvtColor(face,cv2.COLOR_BGR2RGB)
        # Convert cropped frame to a PIL image
        img = Image.fromarray(face)
        # Convert PIL image to ImageTk format
        imgtk2 = ImageTk.PhotoImage(image=img)
        # Update the crop_label with the cropped image
        crop_label.imgtk = imgtk2
        crop_label.configure(image=imgtk2)
    video_label.after(10, update_frame)


def popupError(message):
    popupRoot = Tk()
    popupRoot.title("Lỗi")

    def exit():
        popupRoot.destroy()
    my_font = Font(family="Times New Roman", size=20, weight="bold")
    message = Label(popupRoot, text=message, font=my_font)
    popupButton = Button(popupRoot, text="Ok", bg="Gray", command=exit)
    message.pack()
    popupButton.pack()
    popupRoot.geometry('400x50+700+500')
    popupRoot.mainloop()
def show_popup():
    """Hiển thị popup thông báo."""
    popup = Toplevel(root)
    popup.title("Thông báo")
    popup.geometry("300x100")
    Label(popup, text="Chương trình đang xử lý...", font=("Arial", 12)).pack(pady=20)
    # Khởi chạy công việc trên luồng riêng
    threading.Thread(target=Process, args=(popup,), daemon=True).start()
def Process():
    
    global copy_image
    global face
    face = cv2.cvtColor(face,cv2.COLOR_BGR2RGB)
    cv2.imwrite('face_image.jpg', face)
    count = 0
    while True:
        isFrontSide_image = copy_image[0:0+83, 0:0+132]
            # Tọa độ: (x=53, y=98, w=66, h=56)
        isBackSide_image = copy_image[98:98+56, 53:53+66]
        if isFrontSide(isFrontSide_image):
            print("Mặt Trước")
            # cv2.imshow("Check Zone",isFrontSide_image)
            # Mã Căn Cước Tọa độ: (x=198, y=123, w=179, h=41)
            # Ngày Sinh: Tọa độ: (x=282, y=192, w=163, h=29)
            # Ngày hết hạn: Tọa độ: (x=71, y=268, w=72, h=32)
            x_ID, y_ID, w_ID, h_ID = [190, 92, 187, 35]
            ID_pos = copy_image[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]
            x_date, y_date, w_date, h_date = [275, 151, 118 ,24]
            Date_pos = copy_image[y_date:y_date +h_date, x_date:x_date+w_date]
            ID = ocr_model.ocr(ID_pos)
            Date = ocr_model.ocr(Date_pos)
            try:
                if Date[0][0][1][0] is not None:
                    ID = str(ID[0][0][1][0])
                    Date = str(Date[0][0][1][0]).replace("/", "")
            except TypeError:
                popupError("Vui Lòng Để CCCD Đúng Vị Trí")
                break
            Document_number = ID[3:]
            now = datetime.now().date().year
            DayOfBirth = Date[:2]
            MonthOfBirth = Date[2:4]
            YearOfBirth = ID[4:6]
            Date_of_birth = YearOfBirth+MonthOfBirth+DayOfBirth
            age = (now - int(YearOfBirth))%100
            print(f"Age :{age}")
            if 14 <= age < 23:
                print("Trường Hợp 25t")
                DayOfExpire  = DayOfBirth
                MonthOfExpire = MonthOfBirth
                YearOfExpire = str(25+int(YearOfBirth))
            elif 23 <= age < 38:
                print("Trường Hợp 40t")
                DayOfExpire  = DayOfBirth
                MonthOfExpire = MonthOfBirth
                YearOfExpire = str(40+int(YearOfBirth))
            elif 38 <= age < 58:
                print("Trường Hợp 60t")
                DayOfExpire  = DayOfBirth
                MonthOfExpire = MonthOfBirth
                YearOfExpire = str(60+int(YearOfBirth))
            else:
                print("Trường Hợp Vô Thời Hạn")
                DayOfExpire = '31'
                MonthOfExpire = '12'
                YearOfExpire = "99"
            Day_of_Expire =YearOfExpire+MonthOfExpire+DayOfExpire
            print(f"Date ={Date}")
            print(f"Expire = {DayOfExpire}/{MonthOfExpire}/{str(YearOfExpire)}")
            Facebox.configure(state=NORMAL)
            Facebox.delete(0, END)
            Facebox.insert(END, string="Mặt Trước")
            Facebox.configure(state=DISABLED)

            IDbox.configure(state=NORMAL)
            IDbox.delete(0, END)
            IDbox.insert(END, string=ID)
            IDbox.configure(state=DISABLED)

            Datebox.configure(state=NORMAL)
            Datebox.delete(0, END)
            Datebox.insert(END, string=DayOfBirth+"/"+MonthOfBirth+"/"+YearOfBirth)
            Datebox.configure(state=DISABLED)

            Expirebox.configure(state=NORMAL)
            Expirebox.delete(0, END)
            Expirebox.insert(END, string=DayOfExpire+"/"+MonthOfExpire+"/"+str(YearOfExpire))
            Expirebox.configure(state=DISABLED)

            # cv2.rectangle(cropped_id_card, ((x_ID, y_ID)),
            #               (x_ID+w_ID, y_ID+h_ID), (0, 255, 0), 1, cv2.LINE_AA)

            # cv2.rectangle(cropped_id_card, ((x_date, y_date)),
            #               (x_date+w_date, y_date+h_date), (0, 255, 0), 1, cv2.LINE_AA)
            # cv2.rectangle(cropped_id_card,((71,268)),(71+72,268+32),(0,255,0),1,cv2.LINE_AA)
            # print(f"ID: {ID[0][0][1][0]}")
            # print(f"Date: {Date[0][0][1][0]}")
            # cv2.imshow("Front Position", isFrontSide_image)
            # cv2.imshow("ID_pos", ID_pos)
            print(Document_number)
            print(Date_of_birth)
            print(Day_of_Expire)
            # show_popup()
            readData.getImage(Document_number,Date_of_birth,Day_of_Expire)
            # popup.destroy()  # Đóng popup khi xử lý xong
            break
        elif isBackSide(isBackSide_image):
            print("Mặt sau")
            # cv2.imshow("Check Zone",isBackSide_image)
            # Mã MRZ: Tọa độ: (x=6, y=188, w=487, h=107)
            mrz_pos = copy_image[188:188+107, 6:6+487]
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

            Facebox.configure(state=NORMAL)
            Facebox.delete(0, END)
            Facebox.insert(END, string="Mặt Sau")
            Facebox.configure(state=DISABLED)

            IDbox.configure(state=NORMAL)
            IDbox.delete(0, END)
            IDbox.insert(END, string=Document_number)
            IDbox.configure(state=DISABLED)

            Datebox.configure(state=NORMAL)
            Datebox.delete(0, END)
            Datebox.insert(END, string=Date_of_birth)
            Datebox.configure(state=DISABLED)

            Expirebox.configure(state=NORMAL)
            Expirebox.delete(0, END)
            Expirebox.insert(END, string=Date_of_expire)
            Expirebox.configure(state=DISABLED)
            # show_popup()
            readData.getImage(Document_number,Date_of_birth,Date_of_expire)
            # popup.destroy()  # Đóng popup khi xử lý xong
            # cv2.imshow("Back Position", isBackSide_image)
            # cv2.imshow("mrz_pos", mrz_pos)
            break
        else:
            copy_image = cv2.rotate(copy_image, cv2.ROTATE_180)
            count += 1
            if count >= 10:
                crop_label.configure(image='')

                Facebox.configure(state=NORMAL)
                Facebox.delete(0, END)
                Facebox.insert(END, string="")
                Facebox.configure(state=DISABLED)

                IDbox.configure(state=NORMAL)
                IDbox.delete(0, END)
                IDbox.insert(END, string="")
                IDbox.configure(state=DISABLED)

                Datebox.configure(state=NORMAL)
                Datebox.delete(0, END)
                Datebox.insert(END, string="")
                Datebox.configure(state=DISABLED)

                Expirebox.configure(state=NORMAL)
                Expirebox.delete(0, END)
                Expirebox.insert(END, string="")
                Expirebox.configure(state=DISABLED)
                popupError("Vui Lòng Thử Lại")
                # popup.destroy()  # Đóng popup khi xử lý xong
                break
    facial_image = cv2.imread('output.jpg')
    facial_image = cv2.cvtColor(facial_image,cv2.COLOR_BGR2RGB)
    img_encoding = face_recognition.face_encodings(facial_image)[0]

    real_image = cv2.imread('face_image.jpg')
    real_image = cv2.cvtColor(real_image,cv2.COLOR_BGR2RGB)
    img_encoding2 = face_recognition.face_encodings(real_image)[0]
    rs = face_recognition.compare_faces([img_encoding],img_encoding2)
    print(rs)
    if rs[0] == True:
        popupError("Xác Thực Thành Công")
    else:
        popupError("Xác Thực Thất Bại")
    os.remove("output.jpg")
    os.remove("face_image.jpg")
    # popup.destroy()
def exit_program():

    cap.release()
    root.destroy()


def clear():
    crop_label.configure(image='')

    Facebox.configure(state=NORMAL)
    Facebox.delete(0, END)
    Facebox.insert(END, string="")
    Facebox.configure(state=DISABLED)

    IDbox.configure(state=NORMAL)
    IDbox.delete(0, END)
    IDbox.insert(END, string="")
    IDbox.configure(state=DISABLED)

    Datebox.configure(state=NORMAL)
    Datebox.delete(0, END)
    Datebox.insert(END, string="")
    Datebox.configure(state=DISABLED)

    Expirebox.configure(state=NORMAL)
    Expirebox.delete(0, END)
    Expirebox.insert(END, string="")
    Expirebox.configure(state=DISABLED)
    

exit_button = Button(root, text="Exit", command=exit_program,
                     width=10, height=2, background='Gray', activebackground='Red')
exit_button.place(x=550, y=600)
process_button = Button(root, text="Scan", command=Process,
                        width=10, height=2, background='Gray', activebackground='Green')
process_button.place(x=750, y=600)
clear_button = Button(root, text="Clear", command=clear, width=10,
                      height=2, background='Gray', activebackground='Green')
clear_button.place(x=950, y=600)


update_frame()

root.mainloop()
