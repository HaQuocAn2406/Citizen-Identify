import cv2
from tkinter import *
from tkinter.font import Font
from paddleocr import PaddleOCR
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np
import readData
import os
ocr_model = PaddleOCR(lang='en')
root = Tk()
root.title("Xác Thực CCCD")
root.geometry("1200x750")
video_width, video_height = 500, 300
video_label = Label(root, width=video_width, height=video_height)
video_label.place(x=0, y=0)
crop_label = Label(root, width=video_width, height=video_height)
crop_label.place(x=550, y=0)

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

BAC_label = Label(root, text="BAC")
BAC_label.place(x=20, y=700)
BacBOX = Entry(state=DISABLED, fg='White', width=30)
BacBOX.place(x=100, y=700)

key = 0

cap = cv2.VideoCapture(0)

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


def check_front(image):
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


def check_back(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([40, 255, 255])
    mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    if np.any(mask):
        return True
    else:
        return False


red = [0, 0, 255]
u, p = get_limits(color=red)
print(u, p)


def update_frame():
    global copy_image

    ret, frame = cap.read()
    if ret:

        frame = cv2.resize(frame, (int(video_width), int(video_height)))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        # thresh1 = cv2.adaptiveThreshold(blurred,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
        _, thresh1 = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print(_)
        contours, _ = cv2.findContours(
            thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.imshow("Binary", thresh1)
        # if contours:
        #     # Find the biggest contour based on area
        #     biggest_contour = max(contours, key=cv2.contourArea)

        #     # Use convex hull to get a simpler shape
        #     hull = cv2.convexHull(biggest_contour)

        #     # Approximate the contour to get 4 corners
        #     epsilon = 0.02 * cv2.arcLength(hull, True)
        #     approx = cv2.approxPolyDP(hull, epsilon, True)

        #     # If the approximation has more than 4 points, reduce it to the largest rectangular approximation
        #     if len(approx) >= 3:
        #         rect = cv2.minAreaRect(biggest_contour)
        #         box = cv2.boxPoints(rect)
        #         box = np.int0(box)
        #                 # Top-left point will have the smallest sum, bottom-right will have the largest sum
        #         pts = approx.reshape(4, 2)
        #         s = pts.sum(axis=1)
        #         rect[0] = pts[np.argmin(s)]
        #         rect[2] = pts[np.argmax(s)]
        #         # Top-right point will have the smallest difference, bottom-left will have the largest difference
        #         diff = np.diff(pts, axis=1)
        #         rect[1] = pts[np.argmin(diff)]
        #         rect[3] = pts[np.argmax(diff)]

        #         # Compute the width and height of the new image
        #         width_a = np.linalg.norm(rect[2] - rect[3])
        #         width_b = np.linalg.norm(rect[1] - rect[0])
        #         max_width = max(int(width_a), int(width_b))

        #         height_a = np.linalg.norm(rect[1] - rect[2])
        #         height_b = np.linalg.norm(rect[0] - rect[3])
        #         max_height = max(int(height_a), int(height_b))

        #         # Define the destination points to obtain a "scanned" view
        #         dst = np.array([
        #             [0, 0],
        #             [max_width - 1, 0],
        #             [max_width - 1, max_height - 1],
        #             [0, max_height - 1]
        #         ], dtype="float32")
        #                 # Compute the perspective transform matrix and apply it
        #         matrix = cv2.getPerspectiveTransform(rect, dst)
        #         warped = cv2.warpPerspective(frame, matrix, (max_width, max_height))

        #         # Display or save the cropped and transformed image
        #         cv2.imshow("Scanned Image", warped)
        #     else:
        #         box = approx
        #     # Draw the contour outline
        #     cv2.drawContours(frame, [biggest_contour], -1, (0, 255, 0), 3)
        #     # Draw the four corners
        #     for i, corner in enumerate(box):
        #         print(f"Corner {i+1}: {corner}")
        #         cv2.circle(frame, tuple(corner), 5, (255, 0, 0), -1)  # Mark corners for visualization
        if not contours:
            return update_frame()
        biggest = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(biggest)
        box = cv2.boxPoints(rect).astype('int')
        x, y, w, h = cv2.boundingRect(biggest)
        # cv2.drawContours(frame,[box],-1,(0,0,255),2)
        cv2.rectangle(frame, (x+5, y+5), (x + w-5, y + h-5), (255, 0, 0), 2)
        copy_image = frame[y+5:y+h-5, x+5:x+w-5]
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        imgtk = ImageTk.PhotoImage(image=img)

        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

    video_label.after(1, update_frame)


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


def Process():
    global copy_image
    cropped_id_card = cv2.resize(copy_image, (500, 300))
    check_front_image = cropped_id_card[8:8+91, 14:14+126]
    check_back_image = cropped_id_card[98:98+56, 53:53+66]

    count = 0
    while True:
        # Tọa độ: (x=40, y=17, w=67, h=68)
        check_front_image = cropped_id_card[0:0+90, 0:0+90]
        # Tọa độ: (x=53, y=98, w=66, h=56)
        check_back_image = cropped_id_card[98:98+56, 53:53+66]
        if check_front(check_front_image):
            print("Mặt Trước")
            # cv2.imshow("Check Zone",check_front_image)
            # Mã Căn Cước Tọa độ: (x=198, y=123, w=179, h=41)
            # Ngày Sinh: Tọa độ: (x=282, y=192, w=163, h=29)
            # Ngày hết hạn: Tọa độ: (x=71, y=268, w=72, h=32)
            x_ID, y_ID, w_ID, h_ID = [190, 115, 195, 39]
            ID_pos = cropped_id_card[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]

            x_date, y_date, w_date, h_date = [280, 180, 163, 29]
            Date_pos = cropped_id_card[y_date:y_date +
                                       h_date, x_date:x_date+w_date]
            # Expire_pos = cropped_id_card[268:268+32, 71:71+72]
            # gray_expire = cv2.cvtColor(Expire_pos, cv2.COLOR_BGR2GRAY)
            # gray_date = cv2.cvtColor(Date_pos, cv2.COLOR_BGR2GRAY)
            ID = ocr_model.ocr(ID_pos)
            Date = ocr_model.ocr(Date_pos)
            try:
                if Date[0][0][1][0] is not None:
                    ID = str(ID[0][0][1][0])
                    Date = str(Date[0][0][1][0]).replace("/", "")
            except TypeError:
                popupError("Vui Lòng Để CCCD Đúng Vị Trí")
                break
            # if Date[0][0][1][0] is not None:
            #     ID = str(ID[0][0][1][0])
            #     Date = str(Date[0][0][1][0]).replace("/", "")
            # else:
            #     popupError("Vui Lòng Thử Lại")
            #     break
            now = datetime.now().date().year
            age = now - int(Date[4:])
            Day = Date[:2]
            Month = Date[2:4]
            Year = ID[4:6]

            Year_Expire = 99
            print(f"Age :{age}")
            if 14 <= age < 23:
                print("Trường Hợp 25t")
                Year_Expire = 25+int(Year)
            elif 23 <= age < 38:
                print("Trường Hợp 40t")
                Year_Expire = 40+int(Year)
            elif 38 <= age < 58:
                print("Trường Hợp 60t")
                Year_Expire = 60+int(Year)
            else:
                print("Trường Hợp Vô Thời Hạn")
                Day = '31'
                Month = '12'
                Expire = "99"+Month+Day
            if Year_Expire > 100:
                Year_Expire = str(Year_Expire)
                Year_Expire = Year_Expire[1:]
            print(f"Date ={Date}")
            print(f"Expire = {Day+"/"+Month+"/"+str(Year_Expire)}")
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
            Datebox.insert(END, string=Day+"/"+Month+"/"+Year)
            Datebox.configure(state=DISABLED)

            Expirebox.configure(state=NORMAL)
            Expirebox.delete(0, END)
            Expirebox.insert(END, string=Day+"/"+Month+"/"+str(Year_Expire))
            Expirebox.configure(state=DISABLED)

            # BacBOX.configure(state=NORMAL)
            # BacBOX.delete(0, END)
            # BacBOX.insert(END, string=BAC)
            # BacBOX.configure(state=DISABLED)

            # Expire = ocr_model.ocr(gray_expire)
            # cv2.putText(cropped_id_card, ID, (198, 123),
            #             cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2)
            # cv2.putText(cropped_id_card, Date, (286, 182),
            #             cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2)
            # cv2.putText(cropped_id_card, f"Expire:{Expire}", ((
            #     40, 250)), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2)
            # cv2.putText(cropped_id_card, f"BAC:{
            #             BAC}", (0, 290), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2)

            cv2.rectangle(cropped_id_card, ((x_ID, y_ID)),
                          (x_ID+w_ID, y_ID+h_ID), (0, 255, 0), 1, cv2.LINE_AA)

            cv2.rectangle(cropped_id_card, ((x_date, y_date)),
                          (x_date+w_date, y_date+h_date), (0, 255, 0), 1, cv2.LINE_AA)
            # cv2.rectangle(cropped_id_card,((71,268)),(71+72,268+32),(0,255,0),1,cv2.LINE_AA)
            # print(f"ID: {ID[0][0][1][0]}")
            # print(f"Date: {Date[0][0][1][0]}")
            # cv2.imshow("Front Position", check_front_image)
            # cv2.imshow("ID_pos", ID_pos)
            Document_number = ID[3:]
            Date_of_birth = Year+Month+Day
            Day_of_Expire = str(Year_Expire)+Month+Day
            print(Document_number)
            print(Date_of_birth)
            print(Day_of_Expire)
            readData.getMRZandImage(Document_number,Date_of_birth,Day_of_Expire)
            break
        elif check_back(check_back_image):
            print("Mặt sau")
            # cv2.imshow("Check Zone",check_back_image)
            # Mã MRZ: Tọa độ: (x=6, y=188, w=487, h=107)
            mrz_pos = cropped_id_card[188:188+107, 6:6+487]
            gray_mrz = cv2.cvtColor(mrz_pos, cv2.COLOR_BGR2GRAY)
            mrz = ocr_model.ocr(gray_mrz)
            BAC = ""
            ID = ""
            Date = ""
            Expire = ""
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
            BAC = line[0][5:14]+line[1][:6]+line[1][8:14]

            Facebox.configure(state=NORMAL)
            Facebox.delete(0, END)
            Facebox.insert(END, string="Mặt Sau")
            Facebox.configure(state=DISABLED)

            IDbox.configure(state=NORMAL)
            IDbox.delete(0, END)
            IDbox.insert(END, string=ID)
            IDbox.configure(state=DISABLED)

            Datebox.configure(state=NORMAL)
            Datebox.delete(0, END)
            Datebox.insert(END, string=Date)
            Datebox.configure(state=DISABLED)

            Expirebox.configure(state=NORMAL)
            Expirebox.delete(0, END)
            Expirebox.insert(END, string=Expire)
            Expirebox.configure(state=DISABLED)

            BacBOX.configure(state=NORMAL)
            BacBOX.delete(0, END)
            BacBOX.insert(END, string=BAC)
            BacBOX.configure(state=DISABLED)
            # cv2.imshow("Back Position", check_back_image)
            cv2.imshow("mrz_pos", mrz_pos)
            break
        else:
            cropped_id_card = cv2.rotate(cropped_id_card, cv2.ROTATE_180)
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

                BacBOX.configure(state=NORMAL)
                BacBOX.delete(0, END)
                BacBOX.insert(END, string="")
                BacBOX.configure(state=DISABLED)

                popupError("Vui Lòng Thử Lại")
                break
    facial_image = cv2.imread('output.jpg')
    facial_image = cv2.cvtColor(facial_image,cv2.COLOR_BGR2RGB)
    # Convert cropped frame to a PIL image
    img = Image.fromarray(facial_image)
    # Convert PIL image to ImageTk format
    imgtk = ImageTk.PhotoImage(image=img)
    # Update the crop_label with the cropped image
    crop_label.imgtk = imgtk
    crop_label.configure(image=imgtk)
    os.remove("output.png")

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

    BacBOX.configure(state=NORMAL)
    BacBOX.delete(0, END)
    BacBOX.insert(END, string="")
    BacBOX.configure(state=DISABLED)


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
