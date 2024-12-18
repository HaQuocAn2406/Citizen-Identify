import cv2
import matplotlib.pyplot as plt

# Khởi tạo webcam
cap = cv2.VideoCapture(0)  # 0 là chỉ số mặc định cho webcam chính
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 748)
if not cap.isOpened():
    print("Không thể mở camera.")
    exit()

plt.ion()  # Chế độ tương tác của matplotlib
fig, ax = plt.subplots()

# Tạo một hình ảnh ban đầu (sẽ được cập nhật liên tục)
ret, frame = cap.read()
if not ret:
    print("Không thể đọc khung hình từ camera.")
    cap.release()
    exit()

# Chuyển đổi màu (OpenCV sử dụng BGR, matplotlib sử dụng RGB)
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
img = ax.imshow(frame)

while True:
    # Đọc khung hình từ camera
    ret, frame = cap.read()
    if not ret:
        print("Không thể đọc khung hình từ camera.")
        break

    # Chuyển đổi màu
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Cập nhật hình ảnh
    img.set_data(frame)
    plt.pause(0.01)  # Dừng ngắn để vẽ lại
    plt.draw()

    # Nhấn phím 'q' để thoát
    if plt.waitforbuttonpress(0.01) and plt.get_current_fig_manager().canvas.toolbar.mode == '':
        break

# Giải phóng tài nguyên
cap.release()
plt.close()
