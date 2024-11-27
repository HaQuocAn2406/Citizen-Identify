import cv2
from tkinter import Tk, Label, Frame, PhotoImage, Canvas, Button, StringVar,Toplevel
from PIL import Image, ImageTk
import threading
import numpy as np
from datetime import datetime
from paddleocr import PaddleOCR
import readData
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
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([40, 255, 255])
    mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    if np.any(mask):
        return True
    else:
        return False
def update_video_feed():
    """Cập nhật video từ webcam."""
    global video_label, cap,copy_image
    while True:
        ret, frame = cap.read()
        ret, frame2 = cap2.read()
        frame = cv2.resize(frame,(300,400))
        # frame2 = cv2.resize(frame2,(300,400))
        if ret:
            # Chuyển đổi frame từ BGR sang RGB
            frame2 = cv2.resize(frame2, (int(video_width), int(video_height)))
            # frame2 = cv2.resize(frame2, (int(video_width), int(video_height)))
            gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
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
            # cv2.drawContours(frame,[box],-1,(0,0,255),2)
            cv2.rectangle(frame2, (x+5, y+5), (x + w-5, y + h-5), (255, 0, 0), 2)
            copy_image = frame2[y+5:y+h-5, x+5:x+w-5]

            frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame2))
            video_label.configure(image=frame_image)
            video_label.image = frame_image

def show_popup():
    """Hiển thị popup thông báo."""
    popup = Toplevel(root)
    popup.title("Thông báo")
    popup.geometry("300x100")
    Label(popup, text="Chương trình đang xử lý...", font=("Arial", 12)).pack(pady=20)
    # Khởi chạy công việc trên luồng riêng
    threading.Thread(target=scan_frame, args=(popup,), daemon=True).start()
def scan_frame():
    global copy_image,document_number, full_name, date_of_birth, date_of_expire
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("facial.jpg", frame)
        print("Frame đã được lưu thành 'facial.jpg'")
    cropped_id_card = cv2.resize(copy_image, (500, 300))
    isFrontSide_image = cropped_id_card[8:8+91, 14:14+126]
    isBackSide_image = cropped_id_card[98:98+56, 53:53+66]

    count = 0
    while True:
        # Tọa độ: (x=40, y=17, w=67, h=68)
        isFrontSide_image = cropped_id_card[0:0+90, 0:0+90]
        # Tọa độ: (x=53, y=98, w=66, h=56)
        isBackSide_image = cropped_id_card[98:98+56, 53:53+66]
        if isFrontSide(isFrontSide_image):
            print("Mặt Trước")
            # cv2.imshow("Check Zone",isFrontSide_image)
            # Mã Căn Cước Tọa độ: (x=198, y=123, w=179, h=41)
            # Ngày Sinh: Tọa độ: (x=282, y=192, w=163, h=29)
            # Ngày hết hạn: Tọa độ: (x=71, y=268, w=72, h=32)
            x_ID, y_ID, w_ID, h_ID = [190, 115, 195, 39]
            ID_pos = cropped_id_card[y_ID:y_ID+h_ID, x_ID:x_ID+w_ID]
            x_date, y_date, w_date, h_date = [280, 180, 163, 29]
            Date_pos = cropped_id_card[y_date:y_date +h_date, x_date:x_date+w_date]
            ID = ocr_model.ocr(ID_pos)
            Date = ocr_model.ocr(Date_pos)
            try:
                if Date[0][0][1][0] is not None:
                    ID = str(ID[0][0][1][0])
                    Date = str(Date[0][0][1][0]).replace("/", "")
            except TypeError:
                # popupError("Vui Lòng Để CCCD Đúng Vị Trí")
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
            Date_of_expire =YearOfExpire+MonthOfExpire+DayOfExpire
            print(f"Date ={Date}")
            print(f"Expire = {DayOfExpire}/{MonthOfExpire}/{str(YearOfExpire)}")
            fullname,docID = readData.getImage(Document_number,Date_of_birth,Date_of_expire)
            document_number.set(docID)
            full_name.set(fullname)
            date_of_birth.set(Date_of_birth)
            date_of_expire.set(Date_of_expire)
            image = Image.open("output.jpg")
            image = image.resize((300, 400))  # Thay đổi kích thước ảnh
            photo_image = ImageTk.PhotoImage(image)
            image_label.config(image=photo_image)
            image_label.image = photo_image  # Giữ tham chiếu đến ảnh để tránh mất ảnh
            # popup.destroy()
            break
        elif isBackSide(isBackSide_image):
            print("Mặt sau")
            # cv2.imshow("Check Zone",isBackSide_image)
            # Mã MRZ: Tọa độ: (x=6, y=188, w=487, h=107)
            mrz_pos = cropped_id_card[188:188+107, 6:6+487]
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
            fullname,docID = readData.getImage(Document_number,Date_of_birth,Date_of_expire)
            document_number.set(docID)
            full_name.set(fullname)
            date_of_birth.set(Date_of_birth)
            date_of_expire.set(Date_of_expire)
            image = Image.open("output.jpg")
            image = image.resize((300, 400))  # Thay đổi kích thước ảnh
            photo_image = ImageTk.PhotoImage(image)
            image_label.config(image=photo_image)
            image_label.image = photo_image  # Giữ tham chiếu đến ảnh để tránh mất ảnh
            # popup.destroy()
            break
        else:
            cropped_id_card = cv2.rotate(cropped_id_card, cv2.ROTATE_180)
            count += 1
            if count >= 10:
                break

def clear_info():
    """Xóa thông tin hiển thị."""
    image_label.config(image='')
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
    global cap,cap2, video_label, root, document_number, full_name, date_of_birth, date_of_expire,image_label

    # Khởi tạo tkinter
    root = Tk()
    root.geometry("1200x750")
    root.title("Document Info Viewer")

    # Biến thông tin
    document_number = StringVar(value="")
    full_name = StringVar(value="")
    date_of_birth = StringVar(value="")
    date_of_expire = StringVar(value="")

    # Tạo khung hiển thị ảnh và thông tin
    image_label =Label(root)
    image_label.grid(row=0, column=0, padx=20, pady=20)
    # left_frame = Frame(root, width=300, height=400)
    # left_frame.grid(row=0, column=0, sticky="nw")

    # Hiển thị thông tin bên dưới ảnh chân dung
    Label(root, text="Document Number:", font=("Arial", 12, "bold"), anchor="w").grid(row=1, column=0, sticky="w", padx=5)
    Label(root, textvariable=document_number, font=("Arial", 12), anchor="w").grid(row=1, column=1, sticky="w")

    Label(root, text="Full Name:", font=("Arial", 12, "bold"), anchor="w").grid(row=2, column=0, sticky="w", padx=5)
    Label(root, textvariable=full_name, font=("Arial", 12), anchor="w").grid(row=2, column=1, sticky="w")

    Label(root, text="Date of Birth:", font=("Arial", 12, "bold"), anchor="w").grid(row=3, column=0, sticky="w", padx=5)
    Label(root, textvariable=date_of_birth, font=("Arial", 12), anchor="w").grid(row=3, column=1, sticky="w")

    Label(root, text="Date of Expire:", font=("Arial", 12, "bold"), anchor="w").grid(row=4, column=0, sticky="w", padx=5)
    Label(root, textvariable=date_of_expire, font=("Arial", 12), anchor="w").grid(row=4, column=1, sticky="w")

    # Tạo khung video bên phải
    right_frame = Frame(root, width=150, height=200)
    right_frame.grid(row=0, column=1, sticky="ne")

    # Hiển thị video từ webcam
    video_label = Label(right_frame)
    video_label.pack()

    # Thêm các nút bên dưới
    button_frame = Frame(root)
    button_frame.grid(row=4, column=2, columnspan=2, pady=10,sticky='se')

    Button(button_frame, text="Scan", command=scan_frame, width=10).pack(side="left", padx=5)
    Button(button_frame, text="Clear", command=clear_info, width=10).pack(side="left", padx=5)
    Button(button_frame, text="Exit", command=exit_program, width=10).pack(side="left", padx=5)

    # Khởi động webcam
    cap = cv2.VideoCapture(0)
    cap2 = cv2.VideoCapture(1)
    # Dùng luồng riêng để cập nhật video từ webcam
    video_thread = threading.Thread(target=update_video_feed)
    video_thread.daemon = True
    video_thread.start()

    root.mainloop()


if __name__ == "__main__":
    main()
