import cv2
from tkinter import Tk, Label, Frame, PhotoImage, Canvas, Button, StringVar,Toplevel
from tkinter.font import Font
from PIL import Image, ImageTk
import threading
import numpy as np
from datetime import datetime
from paddleocr import PaddleOCR
import readData
from readCard import*
import face_recognition
import os
import time
ocr_model = PaddleOCR(lang='en')
video_width, video_height = 500, 300
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
    lower_yellow = np.array([10, 80, 80])
    upper_yellow = np.array([30, 255, 255])
    mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    if np.any(mask):
        return True
    else:
        return False
def update_video_feed():
    """Cập nhật video từ webcam."""
    global video_label,face_label, cap,copy_image
    # while True:
    ret, frame = cap.read()
    ret, frame2 = cap2.read()
    frame = cv2.resize(frame,(500,300))
    frame2 = cv2.resize(frame2,(500,300))
    if ret:
            # # Chuyển đổi frame từ BGR sang RGB
            # frame = cv2.resize(frame, (int(video_width), int(video_height)))
            # frame = cv2.resize(frame, (int(video_width), int(video_height)))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh1 = cv2.threshold(blurred, 0, 250, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return update_video_feed()
            biggest = max(contours, key=cv2.contourArea)
            rect = cv2.minAreaRect(biggest)
            box = cv2.boxPoints(rect).astype('int')
            x, y, w, h = cv2.boundingRect(biggest)
            cv2.drawContours(frame,[box],-1,(0,0,255),2)
            cv2.rectangle(frame, (x+5, y+5), (x + w-5, y + h-5), (255, 0, 0), 2)
            # copy_image = frame2
            copy_image = frame[y+5:y+h-5, x+5:x+w-5]
            frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame2))
            video_label.configure(image=frame_image)
            video_label.image = frame_image

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image2 = ImageTk.PhotoImage(image=Image.fromarray(frame))
            face_label.configure(image=frame_image2)
            face_label.image = frame_image2
    cv2.imshow("Binary",thresh1)
    video_label.after(1, update_video_feed)

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
def scan_frame():
    global copy_image,document_number, full_name, date_of_birth, date_of_expire
    root.after(500, clear_info())
    ret, frame = cap2.read()
    if ret:
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        cv2.imwrite("facial.jpg", frame)
        print("Frame đã được lưu thành 'facial.jpg'")
    # cropped_id_card = cv2.resize(copy_image, (500, 300))
    Document_number, Date_of_birth, Date_of_expire = read(copy_image)
    date_of_birth.set(Date_of_birth)
    date_of_expire.set(Date_of_expire)
    fullname,docID = readData.getImage(Document_number,Date_of_birth,Date_of_expire)
    document_number.set(docID)
    full_name.set(fullname)
    facial_image = cv2.imread('output.jpg')
    facial_image = cv2.cvtColor(facial_image,cv2.COLOR_BGR2RGB)
    img_encoding = face_recognition.face_encodings(facial_image)[0]

    real_image = cv2.imread('facial.jpg')
    real_image = cv2.cvtColor(real_image,cv2.COLOR_BGR2RGB)
    img_encoding2 = face_recognition.face_encodings(real_image)[0]
    rs = face_recognition.compare_faces([img_encoding],img_encoding2)
    print(rs)
    if rs[0] == True:
        popupError("Xác Thực Thành Công")
    else:
        popupError("Xác Thực Thất Bại")
    os.remove("output.jpg")
    os.remove("facial.jpg")

def clear_info():
    """Xóa thông tin hiển thị."""
    # image_label.config(image='')
    document_number.set("")
    full_name.set("")
    date_of_birth.set("")
    date_of_expire.set("")

def exit_program():
    """Thoát chương trình."""
    cap.release()
    cv2.destroyAllWindows()
    root.quit()


def main():
    global cap,cap2, video_label,face_label, root, document_number, full_name, date_of_birth, date_of_expire,image_label
    # Khởi động webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
    cap2 = cv2.VideoCapture(1)
    # Khởi tạo tkinter
    root = Tk()
    root.geometry("1024x768")
    root.rowconfigure(0, weight=5)  # Dòng chứa hình ảnh chiếm 80% chiều cao
    root.rowconfigure(1, weight=0)  # Dòng chứa thông tin chiếm 20% chiều cao
    root.rowconfigure(2, weight=0)  # Dòng chứa nút không chiếm thêm không gian
    root.columnconfigure(0, weight=0)
    root.title("Document Info Viewer")
    # Biến thông tin
    document_number = StringVar(value="test value")
    full_name = StringVar(value="test value")
    date_of_birth = StringVar(value="test value")
    date_of_expire = StringVar(value="test value")
    nation = StringVar(value="test value")

    # Khu vực hiển thị thông tin
    frame_bottom = Frame(root)
    frame_bottom.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    Document_Number_label = Label(frame_bottom, text="Document Number:",font=("Arial", 12, "bold"), anchor="sw")
    Document_Number_label.grid(row=0, column=0, sticky="sw", pady=5)

    Full_Name_label = Label(frame_bottom, text="Full Name:",font=("Arial", 12, "bold"), anchor="sw")
    Full_Name_label.grid(row=1, column=0, sticky="sw", pady=5)

    Nation_label = Label(frame_bottom, text="Nation:",font=("Arial", 12, "bold"), anchor="sw")
    Nation_label.grid(row=2, column=0, sticky="sw", pady=5)

    Date_Of_Birth_label = Label(frame_bottom, text="Date Of Birth:",font=("Arial", 12, "bold"), anchor="sw")
    Date_Of_Birth_label.grid(row=3, column=0, sticky="sw", pady=5)

    Date_Of_Expire_label = Label(frame_bottom, text="Date Of Expire:",font=("Arial", 12, "bold"), anchor="sw")
    Date_Of_Expire_label.grid(row=4, column=0, sticky="sw", pady=5)

    Document_Number_value = Label(frame_bottom, textvariable=document_number,font=("Arial", 12, "bold"), anchor="sw")
    Document_Number_value.grid(row=0, column=1, sticky="sw", pady=5)

    Full_Name_value = Label(frame_bottom, textvariable=full_name,font=("Arial", 12, "bold"), anchor="sw")
    Full_Name_value.grid(row=1, column=1, sticky="sw", pady=5)

    Nation_value = Label(frame_bottom, textvariable=nation, font=("Arial", 12, "bold"),anchor="sw")
    Nation_value.grid(row=2, column=1, sticky="sw", pady=5)

    Date_Of_Birth_value = Label(frame_bottom, textvariable=date_of_birth,font=("Arial", 12, "bold"), anchor="sw")
    Date_Of_Birth_value.grid(row=3, column=1, sticky="sw", pady=5)

    Date_Of_Expire_value = Label(frame_bottom, textvariable=date_of_expire, font=("Arial", 12, "bold"),anchor="sw")
    Date_Of_Expire_value.grid(row=4, column=1, sticky="sw", pady=5)

    # Khu vực hiển thị hình ảnh
    frame_top = Frame(root)
    frame_top.grid(row=0, column=0, sticky="nsew")

    frame_top.columnconfigure((0, 1), weight=1)
    frame_top.rowconfigure(0, weight=1)

    video_label = Label(frame_top, text="ID Card", bg="black", fg="white")
    video_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    face_label = Label(frame_top, text="Facial", bg="black", fg="white")
    face_label.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    # Thêm các nút bên dưới
    frame_buttons = Frame(root)
    frame_buttons.grid(row=4, column=0, sticky="e", padx=10, pady=10)
    frame_bottom.columnconfigure((0, 1), weight=1)
    
    btn_exit = Button(frame_bottom, text="Exit", command=exit_program, width=15, height=2)
    btn_exit.grid(row=4, column=2, padx=5,sticky="se")

    btn_clear = Button(frame_bottom, text="Clear", command=clear_info,width=15, height=2)
    btn_clear.grid(row=4, column=3, padx=5,sticky="se")

    btn_scan = Button(frame_bottom, text="Scan", command=scan_frame,width=15, height=2)
    btn_scan.grid(row=4, column=4, padx=5,sticky="se")
    update_video_feed()
    root.mainloop()


if __name__ == "__main__":
    main()
    
