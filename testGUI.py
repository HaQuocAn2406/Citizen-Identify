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
    while True:
        ret, frame = cap.read()
        ret, frame2 = cap2.read()
        frame = cv2.resize(frame,(500,300))
        frame2 = cv2.resize(frame2,(500,300))
        if ret:
            # # Chuyển đổi frame từ BGR sang RGB
            # frame = cv2.resize(frame, (int(video_width), int(video_height)))
            # frame = cv2.resize(frame, (int(video_width), int(video_height)))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            # thresh1 = cv2.adaptiveThreshold(blurred,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
            _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
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

    # Khởi tạo tkinter
    root = Tk()
    # root.geometry("1200x750")
    root.title("Document Info Viewer")

    # Biến thông tin
    document_number = StringVar(value="")
    full_name = StringVar(value="")
    date_of_birth = StringVar(value="")
    date_of_expire = StringVar(value="")

    # left_frame = Frame(root, width=300, height=400)
    # left_frame.grid(row=0, column=0, sticky="nw")

    # Hiển thị thông tin bên dưới ảnh chân dung
    Label(root, text="Document Number:", font=("Arial", 12, "bold"), anchor="sw").grid(row=1, column=0, sticky="sw", padx=5)
    Label(root, textvariable=document_number, font=("Arial", 12), anchor="sw").grid(row=1, column=1, sticky="sw")

    Label(root, text="Full Name:", font=("Arial", 12, "bold"), anchor="sw").grid(row=2, column=0, sticky="sw", padx=5)
    Label(root, textvariable=full_name, font=("Arial", 12), anchor="sw").grid(row=2, column=1, sticky="sw")

    Label(root, text="Date of Birth:", font=("Arial", 12, "bold"), anchor="sw").grid(row=3, column=0, sticky="sw", padx=5)
    Label(root, textvariable=date_of_birth, font=("Arial", 12), anchor="sw").grid(row=3, column=1, sticky="sw")

    Label(root, text="Date of Expire:", font=("Arial", 12, "bold"), anchor="sw").grid(row=4, column=0, sticky="sw", padx=5)
    Label(root, textvariable=date_of_expire, font=("Arial", 12), anchor="sw").grid(row=4, column=1, sticky="sw")

    # Tạo khung video bên phải
    right_frame = Frame(root, width=1200,height=750)
    right_frame.grid(row=0, column=0, sticky="ne")
    left_frame =Frame(root,width=1200,height=750)
    left_frame.grid(row=0, column=2, sticky="nw")
    # Hiển thị video từ webcam
    video_label = Label(right_frame)
    video_label.pack()
    # Tạo khung hiển thị ảnh và thông tin

    face_label = Label(left_frame)
    face_label.pack()
    # Thêm các nút bên dưới
    button_frame = Frame(root)
    button_frame.grid(row=4, column=2, columnspan=2, pady=10,sticky='se')

    Button(button_frame, text="Scan", command=scan_frame, width=10).pack(side="left", padx=5)
    Button(button_frame, text="Clear", command=clear_info, width=10).pack(side="left", padx=5)
    Button(button_frame, text="Exit", command=exit_program, width=10).pack(side="left", padx=5)

    # Khởi động webcam
    cap = cv2.VideoCapture(1)
    cap2 = cv2.VideoCapture(0)
    # Dùng luồng riêng để cập nhật video từ webcam
    video_thread = threading.Thread(target=update_video_feed)
    video_thread.daemon = True
    video_thread.start()

    root.mainloop()


if __name__ == "__main__":
    main()
