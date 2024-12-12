import cv2
from tkinter import Tk, Label, Frame, PhotoImage, Canvas, Button, StringVar, Toplevel
from tkinter.font import Font
from PIL import Image, ImageTk
import threading
import numpy as np
from datetime import datetime
from paddleocr import PaddleOCR
import readData
from readCard import *
import face_recognition
import os
import time
from picamera2 import Picamera2
ocr_model = PaddleOCR(lang='en')
video_width, video_height = 500, 300


def update_video_feed():
    global copy_image
    # self.frame2 = self.picam2.capture_array()
    ret, frame = cap.read()
    frame2 = frame2 = picam2.capture_array()
    frame = cv2.resize(frame, (500, 300))
    frame2 = cv2.resize(frame2, (444, 261))
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh1 = cv2.threshold(
            blurred, 0, 250, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(
            thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return update_video_feed()
        biggest = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(biggest)
        box = cv2.boxPoints(rect).astype('int')
        x, y, w, h = cv2.boundingRect(biggest)
        cv2.drawContours(frame, [box], -1, (0, 0, 255), 2)
        cv2.rectangle(frame, (x+5, y+5), (x + w-5, y + h-5), (255, 0, 0), 2)
        copy_image = frame[y+5:y+h-5, x+5:x+w-5]
        frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
        frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame2))
        Video_Webcam.imgtk = frame_image
        Video_Webcam.configure(image=frame_image)
    WebcamFrame.after(1, update_video_feed)

def popupError(message):
        global popup
        popup = Toplevel(root)
        popup.title("Notification")
        popup.geometry("300x200")
        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_w = root.winfo_width()
        root_h = root.winfo_height()
        popup_w , popup_h=200,200
        x = root_x+(root_w//2)-(popup_w//2)
        y = root_y+(root_h//2)-(popup_h//2)
        popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")
        Label(popup,text=message,font=("Arial",14)).pack(pady=50)

def scan_frame():
    clear_info()
    frame2 = picam2.capture_array()
    frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
    cv2.imwrite("facial.jpg", frame2)
    base_image=cv2.imread("facial.jpg")
    base_image= cv2.cvtColor(base_image,cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(base_image)
    if len(face_locations) == 0 or len(face_locations) > 1:
        popup.destroy()
        popupError("Cant Detect Face")
        return
    else:
        print("Frame ÄÃ£ ÄÆ°á»£c lÆ°u thÃ nh 'facial.jpg'")
        popupError("Processing")
        thread = threading.Thread(target=process_frame)
        thread.daemon = True
        thread.start()
        
def compare_face():
    image_from_card = cv2.imread('output.jpg')
    image_from_card = cv2.cvtColor(image_from_card, cv2.COLOR_BGR2RGB)
    real_image = cv2.imread('facial.jpg')
    real_image = cv2.cvtColor(real_image, cv2.COLOR_BGR2RGB)
    img_encoding2 = face_recognition.face_encodings(real_image)[0]
    img_encoding = face_recognition.face_encodings(image_from_card)[0]
    rs = face_recognition.compare_faces([img_encoding], img_encoding2)
    print(rs)
    popup.destroy()
    if rs[0] == True:
        popupError("Success")
    else:
        popupError("Fail")
    os.remove("output.jpg")
    os.remove("facial.jpg")
def process_frame():
    global copy_image, document_number, full_name, date_of_birth, date_of_expire
    # Hiá»n thá» áº£nh
#    plt.imshow(copy_image)
 #   plt.axis('on')
  #  plt.show()
    try:
        Document_number, Date_of_birth, Date_of_expire = read(copy_image)
    except Exception:
        popup.destroy()
        popupError("Error When Read OCR")
        time.sleep(2)
        popup.destroy()
    date_of_birth.set(Date_of_birth)
    date_of_expire.set(Date_of_expire)
    try:
        fullname, docID,nguyen_quan = readData.getImage(Document_number, Date_of_birth, Date_of_expire)
    except Exception:
        popup.destroy()
        popupError("Authentication Error")
        time.sleep(2)
        popup.destroy()
    nation.set(nguyen_quan)
    document_number.set(docID)
    full_name.set(fullname)
    image_from_card = cv2.imread('output.jpg')
    image_from_card = cv2.cvtColor(image_from_card, cv2.COLOR_BGR2RGB)
    image_from_card_cp = cv2.resize(image_from_card,(150,200))
    image_from_card_cp = ImageTk.PhotoImage(image=Image.fromarray(image_from_card_cp))
    FacialLabel.imgtk = image_from_card_cp
    FacialLabel.configure(image=image_from_card_cp)


    compare_face()

def clear_info():
    FacialLabel.configure(image="")
    document_number.set("")
    nation.set("")
    full_name.set("")
    date_of_birth.set("")
    date_of_expire.set("")

def exit_program():
    cap.release()
    # cap2.release()
    cv2.destroyAllWindows()
    root.quit()

def main():
    global cap, picam2, FacialLabel, nation, root, document_number, full_name, date_of_birth, date_of_expire, Video_Webcam, WebcamFrame
    # Khá»i táº¡o tkinter

    root = Tk()
    root.geometry("1024x600")
    root.rowconfigure(0, weight=5)  # DÃ²ng chá»©a hÃ¬nh áº£nh chiáº¿m 80% chiá»u cao
    root.rowconfigure(1, weight=0)  # DÃ²ng chá»©a thÃ´ng tin chiáº¿m 20% chiá»u cao
    root.rowconfigure(2, weight=0)  # DÃ²ng chá»©a nÃºt khÃ´ng chiáº¿m thÃªm khÃ´ng gian
    root.columnconfigure(0, weight=0)
    root.title("Document Info Viewer")
    # Biáº¿n thÃ´ng tin
    root.geometry("1024x748")
    #  root.attributes("-fullscreen", True)
    #  root.minsize(120, 1)
    #  root.maxsize(1540, 845)
    #  root.resizable(1,  1)
    root.title("Toplevel 0")
    root.configure(background="#d9d9d9")
    root.configure(highlightbackground="#d9d9d9")
    root.configure(highlightcolor="#000000")
    document_number = StringVar()
    full_name = StringVar()
    nation = StringVar()
    date_of_birth = StringVar()
    date_of_expire = StringVar()

    Title = Label(root)
    Title.place(relx=0.381, rely=0.033, height=31, width=274)
    Title.configure(activebackground="#d9d9d9")
    Title.configure(activeforeground="black")
    Title.configure(anchor='w')
    Title.configure(background="#d9d9d9")
    Title.configure(compound='left')
    Title.configure(disabledforeground="#a3a3a3")
    Title.configure(font="-family {Times New Roman} -size 23 -weight bold")
    Title.configure(foreground="black")
    Title.configure(highlightbackground="#d9d9d9")
    Title.configure(highlightcolor="#000000")
    Title.configure(text='Final Project')

    SubTitle = Label(root)
    SubTitle.place(relx=0.225, rely=0.1, height=21, width=694)
    SubTitle.configure(activebackground="#d9d9d9")
    SubTitle.configure(activeforeground="black")
    SubTitle.configure(anchor='w')
    SubTitle.configure(background="#d9d9d9")
    SubTitle.configure(compound='left')
    SubTitle.configure(disabledforeground="#a3a3a3")
    SubTitle.configure(font="-family {Times New Roman} -size 14 -weight bold")
    SubTitle.configure(foreground="black")
    SubTitle.configure(highlightbackground="#d9d9d9")
    SubTitle.configure(highlightcolor="#000000")
    SubTitle.configure( text='Design of an ID face authentication system using image processing and chip-embedded citizen identification cards')

    WebcamFrame = Frame(root)
    WebcamFrame.place(relx=0.01, rely=0.217,height=287, width=469)
    WebcamFrame.configure(relief='groove')
    WebcamFrame.configure(borderwidth="2")
    WebcamFrame.configure(relief="groove")
    WebcamFrame.configure(background="#d9d9d9")
    WebcamFrame.configure(highlightbackground="#d9d9d9")
    WebcamFrame.configure(highlightcolor="#000000")

    Video_Webcam = Label(WebcamFrame)
    Video_Webcam.place(relx=0.021, rely=0.035, height=261, width=444)
    Video_Webcam.configure(activebackground="#d9d9d9")
    Video_Webcam.configure(activeforeground="black")
    Video_Webcam.configure(anchor='nw')
    Video_Webcam.configure(background="#d9d9d9")
    Video_Webcam.configure(compound='left')
    Video_Webcam.configure(disabledforeground="#a3a3a3")
    Video_Webcam.configure(foreground="black")
    Video_Webcam.configure(highlightbackground="#d9d9d9")
    Video_Webcam.configure(highlightcolor="#000000")
    Video_Webcam.configure(text="")

    cap = cv2.VideoCapture(0)
    # cap2 = cv2.VideoCapture(1)
    picam2 = Picamera2()

        # Configure the camera
    preview_config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
    picam2.configure(preview_config)

    config = picam2.camera_config.copy()

    picam2.start()
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 748)

    update_video_feed()

    Logo = Label(root)
    Logo.place(relx=0.01, rely=0.017, height=100, width=106)
    Logo.configure(activebackground="#d9d9d9")
    Logo.configure(activeforeground="black")
    Logo.configure(anchor='w')
    Logo.configure(background="#d9d9d9")
    Logo.configure(compound='left')
    Logo.configure(disabledforeground="#a3a3a3")
    Logo.configure(foreground="#000000")
    Logo.configure(highlightbackground="#d9d9d9")
    Logo.configure(highlightcolor="#000000")
    _location = os.path.dirname(__file__)
    photo_location = os.path.join(_location, "TDTU_resize-removebg-preview.png")
    global _img0
    _img0 = PhotoImage(file=photo_location)
    Logo.configure(image=_img0)

    CheckButton = Button(root)
    CheckButton.place(relx=0.029, rely=0.85, height=46, width=97)
    CheckButton.configure(activebackground="#d9d9d9")
    CheckButton.configure(activeforeground="black")
    CheckButton.configure(background="#6dfd44")
    CheckButton.configure(disabledforeground="#a3a3a3")
    CheckButton.configure(foreground="black")
    CheckButton.configure(highlightbackground="#d9d9d9")
    CheckButton.configure(highlightcolor="#000000")
    CheckButton.configure(text='Check')
    CheckButton.configure(command=scan_frame)

    ClearButton = Button(root)
    ClearButton.place(relx=0.166, rely=0.85, height=46, width=97)
    ClearButton.configure(activebackground="#d9d9d9")
    ClearButton.configure(activeforeground="black")
    ClearButton.configure(background="#fff424")
    ClearButton.configure(disabledforeground="#a3a3a3")
    ClearButton.configure(foreground="black")
    ClearButton.configure(highlightbackground="#d9d9d9")
    ClearButton.configure(highlightcolor="#000000")
    ClearButton.configure(text='''Clear''')
    ClearButton.configure(command=clear_info)

    ExitButton = Button(root)
    ExitButton.place(relx=0.303, rely=0.85, height=46, width=97)
    ExitButton.configure(activebackground="#d9d9d9")
    ExitButton.configure(activeforeground="black")
    ExitButton.configure(background="#ff243a")
    ExitButton.configure(disabledforeground="#a3a3a3")
    ExitButton.configure(foreground="black")
    ExitButton.configure(highlightbackground="#d9d9d9")
    ExitButton.configure(highlightcolor="#000000")
    ExitButton.configure(text='''Exit''')
    ExitButton.configure(command=exit_program)

    InforFrame = Frame(root)
    InforFrame.place(relx=0.488, rely=0.167,
                     relheight=0.792, relwidth=0.437)
    InforFrame.configure(relief='groove')
    InforFrame.configure(borderwidth="2")
    InforFrame.configure(relief="groove")
    InforFrame.configure(background="#d9d9d9")
    InforFrame.configure(highlightbackground="#d9d9d9")
    InforFrame.configure(highlightcolor="#000000")

    FacialLabel = Label(InforFrame)
    FacialLabel.place(relx=0.357, rely=0.021, height=200, width=151)
    FacialLabel.configure(activebackground="#d9d9d9")
    FacialLabel.configure(activeforeground="black")
    FacialLabel.configure(anchor='w')
    FacialLabel.configure(background="#d9d9d9")
    FacialLabel.configure(compound='left')
    FacialLabel.configure(disabledforeground="#a3a3a3")
    FacialLabel.configure(foreground="black")
    FacialLabel.configure(highlightbackground="#d9d9d9")
    FacialLabel.configure(highlightcolor="#000000")
    facial_image = cv2.resize(cv2.imread("TDTU_resize-removebg-preview.png"), (150, 200))
    facial_image_RGB = cv2.cvtColor(facial_image, cv2.COLOR_BGR2RGB)
    facial = ImageTk.PhotoImage(image=Image.fromarray(facial_image_RGB))
    FacialLabel.configure(image=facial)

    FullNameLabel = Label(InforFrame)
    FullNameLabel.place(relx=0.045, rely=0.611, height=21, width=84)
    FullNameLabel.configure(activebackground="#d9d9d9")
    FullNameLabel.configure(activeforeground="black")
    FullNameLabel.configure(anchor='w')
    FullNameLabel.configure(background="#d9d9d9")
    FullNameLabel.configure(compound='left')
    FullNameLabel.configure(disabledforeground="#a3a3a3")
    FullNameLabel.configure(font="-family {Times New Roman} -size 13")
    FullNameLabel.configure(foreground="black")
    FullNameLabel.configure(highlightbackground="#d9d9d9")
    FullNameLabel.configure(highlightcolor="#000000")
    FullNameLabel.configure(text='''Full Name:''')

    NationLabel = Label(InforFrame)
    NationLabel.place(relx=0.045, rely=0.674, height=21, width=110)
    NationLabel.configure(activebackground="#d9d9d9")
    NationLabel.configure(activeforeground="black")
    NationLabel.configure(anchor='w')
    NationLabel.configure(background="#d9d9d9")
    NationLabel.configure(compound='left')
    NationLabel.configure(disabledforeground="#a3a3a3")
    NationLabel.configure(font="-family {Times New Roman} -size 13")
    NationLabel.configure(foreground="black")
    NationLabel.configure(highlightbackground="#d9d9d9")
    NationLabel.configure(highlightcolor="#000000")
    NationLabel.configure(text='''Original Place:''')

    DoBLabel = Label(InforFrame)
    DoBLabel.place(relx=0.045, rely=0.737, height=21, width=104)
    DoBLabel.configure(activebackground="#d9d9d9")
    DoBLabel.configure(activeforeground="black")
    DoBLabel.configure(anchor='w')
    DoBLabel.configure(background="#d9d9d9")
    DoBLabel.configure(compound='left')
    DoBLabel.configure(disabledforeground="#a3a3a3")
    DoBLabel.configure(font="-family {Times New Roman} -size 13")
    DoBLabel.configure(foreground="black")
    DoBLabel.configure(highlightbackground="#d9d9d9")
    DoBLabel.configure(highlightcolor="#000000")
    DoBLabel.configure(text='''Date Of Birth:''')

    DoELabel = Label(InforFrame)
    DoELabel.place(relx=0.045, rely=0.8, height=21, width=114)
    DoELabel.configure(activebackground="#d9d9d9")
    DoELabel.configure(activeforeground="black")
    DoELabel.configure(anchor='w')
    DoELabel.configure(background="#d9d9d9")
    DoELabel.configure(compound='left')
    DoELabel.configure(disabledforeground="#a3a3a3")
    DoELabel.configure(font="-family {Times New Roman} -size 13")
    DoELabel.configure(foreground="black")
    DoELabel.configure(highlightbackground="#d9d9d9")
    DoELabel.configure(highlightcolor="#000000")
    DoELabel.configure(text='''Date Of Expire:''')

    DocumentNumLabel = Label(InforFrame)
    DocumentNumLabel.place(relx=0.045, rely=0.526, height=41, width=144)
    DocumentNumLabel.configure(activebackground="#d9d9d9")
    DocumentNumLabel.configure(activeforeground="black")
    DocumentNumLabel.configure(anchor='w')
    DocumentNumLabel.configure(background="#d9d9d9")
    DocumentNumLabel.configure(compound='left')
    DocumentNumLabel.configure(disabledforeground="#a3a3a3")
    DocumentNumLabel.configure(font="-family {Times New Roman} -size 13")
    DocumentNumLabel.configure(foreground="black")
    DocumentNumLabel.configure(highlightbackground="#d9d9d9")
    DocumentNumLabel.configure(highlightcolor="#000000")
    DocumentNumLabel.configure(text='''Document Number:''')

    DocVarLabel = Label(InforFrame)
    DocVarLabel.place(relx=0.38, rely=0.547, height=21, width=154)
    DocVarLabel.configure(font="-family {Times New Roman} -size 13")
    DocVarLabel.configure(activebackground="#d9d9d9")
    DocVarLabel.configure(activeforeground="black")
    DocVarLabel.configure(anchor='w')
    DocVarLabel.configure(background="#d9d9d9")
    DocVarLabel.configure(compound='left')
    DocVarLabel.configure(disabledforeground="#a3a3a3")
    DocVarLabel.configure(foreground="black")
    DocVarLabel.configure(highlightbackground="#d9d9d9")
    DocVarLabel.configure(highlightcolor="#000000")
    DocVarLabel.configure(text='''DocumentNumVar''')
    DocVarLabel.configure(textvariable=document_number)

    NameVarLabel = Label(InforFrame)
    NameVarLabel.place(relx=0.246, rely=0.611, height=21, width=164)
    NameVarLabel.configure(font="-family {Times New Roman} -size 13")
    NameVarLabel.configure(activebackground="#d9d9d9")
    NameVarLabel.configure(activeforeground="black")
    NameVarLabel.configure(anchor='w')
    NameVarLabel.configure(background="#d9d9d9")
    NameVarLabel.configure(compound='left')
    NameVarLabel.configure(disabledforeground="#a3a3a3")
    NameVarLabel.configure(foreground="black")
    NameVarLabel.configure(highlightbackground="#d9d9d9")
    NameVarLabel.configure(highlightcolor="#000000")
    NameVarLabel.configure(text='''FullNameVar''')
    NameVarLabel.configure(textvariable=full_name)

    NationVarLabel = Label(InforFrame)
    NationVarLabel.place(relx=0.301, rely=0.674, height=21, width=164)
    NationVarLabel.configure(font="-family {Times New Roman} -size 13")
    NationVarLabel.configure(activebackground="#d9d9d9")
    NationVarLabel.configure(activeforeground="black")
    NationVarLabel.configure(anchor='w')
    NationVarLabel.configure(background="#d9d9d9")
    NationVarLabel.configure(compound='left')
    NationVarLabel.configure(disabledforeground="#a3a3a3")
    NationVarLabel.configure(foreground="black")
    NationVarLabel.configure(highlightbackground="#d9d9d9")
    NationVarLabel.configure(highlightcolor="#000000")
    NationVarLabel.configure(text='''NationVar''')
    NationVarLabel.configure(textvariable=nation)

    DoBVarLabel = Label(InforFrame)
    
    DoBVarLabel.place(relx=0.291, rely=0.737, height=21, width=144)
    DoBVarLabel.configure(font="-family {Times New Roman} -size 13")
    DoBVarLabel.configure(activebackground="#d9d9d9")
    DoBVarLabel.configure(activeforeground="black")
    DoBVarLabel.configure(anchor='w')
    DoBVarLabel.configure(background="#d9d9d9")
    DoBVarLabel.configure(compound='left')
    DoBVarLabel.configure(disabledforeground="#a3a3a3")
    DoBVarLabel.configure(foreground="black")
    DoBVarLabel.configure(highlightbackground="#d9d9d9")
    DoBVarLabel.configure(highlightcolor="#000000")
    DoBVarLabel.configure(text='''DoB''')
    DoBVarLabel.configure(textvariable=date_of_birth)

    DoEVar = Label(InforFrame)
    DoEVar.configure(font="-family {Times New Roman} -size 13")
    DoEVar.place(relx=0.336, rely=0.8, height=21, width=134)
    DoEVar.configure(activebackground="#d9d9d9")
    DoEVar.configure(activeforeground="black")
    DoEVar.configure(anchor='w')
    DoEVar.configure(background="#d9d9d9")
    DoEVar.configure(compound='left')
    DoEVar.configure(disabledforeground="#a3a3a3")
    DoEVar.configure(foreground="black")
    DoEVar.configure(highlightbackground="#d9d9d9")
    DoEVar.configure(highlightcolor="#000000")
    DoEVar.configure(text='''DoE''')
    DoEVar.configure(textvariable=date_of_expire)
    
    root.mainloop()

if __name__ == "__main__":
    main()
