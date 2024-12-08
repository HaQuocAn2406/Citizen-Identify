# import cv2
# import face_recognition
# import tkinter as tk
# from PIL import Image, ImageTk

# def detect_faces():
#     ret, frame = cap.read()
#     frame = cv2.resize(frame,(500,300))
#     if not ret:
#         return
    
#     # Resize frame for faster processing
#     small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
#     rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

#     # Detect faces
#     face_locations = face_recognition.face_locations(rgb_frame)

#     # Check number of faces
#     if len(face_locations) == 0 or len(face_locations) > 1:
#         message_label.config(text="Vui lòng canh chỉnh để DUY NHẤT gương mặt trong khung hình")
#     else:
#         message_label.config(text="Gương mặt hợp lệ!")

#     # Draw rectangles around faces
#     for top, right, bottom, left in face_locations:
#         top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
#         cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

#     # Convert frame to ImageTk for Tkinter
#     img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     img = Image.fromarray(img)
#     imgtk = ImageTk.PhotoImage(image=img)

#     # Update the label widget
#     video_label.imgtk = imgtk
#     video_label.configure(image=imgtk)

#     # Call detect_faces again after a delay
#     video_label.after(1, detect_faces)

# # Initialize webcam
# cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2592)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1944)
# # Create Tkinter window
# root = tk.Tk()
# root.title("Face Detection")

# # Create video display label
# video_label = tk.Label(root)
# video_label.pack()

# # Create message display label
# message_label = tk.Label(root, text="", font=("Arial", 14), fg="red")
# message_label.pack()

# # Start face detection
# detect_faces()

# # Run Tkinter event loop
# root.mainloop()

# # Release webcam when the program exits
# cap.release()
# cv2.destroyAllWindows()


import tkinter as tk

def open_popup():
    # Create a popup window
    popup = tk.Toplevel(root)
    popup.title("Popup Window")
    popup.geometry("300x200")  # Set the popup window size
    
    # Get the dimensions and position of the main window
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    
    # Get the popup window dimensions
    popup_width = 300
    popup_height = 200
    
    # Calculate the x and y position to center the popup relative to the main window
    x = root_x + (root_width // 2) - (popup_width // 2)
    y = root_y + (root_height // 2) - (popup_height // 2)
    
    # Set the popup window's geometry
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    
    # Add a label to the popup
    tk.Label(popup, text="This is a popup!", font=("Arial", 14)).pack(pady=50)
    
    # Add a close button
    tk.Button(popup, text="Close", command=popup.destroy).pack()

# Create the main window
root = tk.Tk()
root.title("Main Window")
root.geometry("1024x600")  # Set the main window size

# Add a button to open the popup
tk.Button(root, text="Open Popup", command=open_popup).pack(pady=50)

# Run the main loop
root.mainloop()

