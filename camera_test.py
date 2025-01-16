import cv2
for i in range(0, 32):  # Assuming you want to test video0 to video22
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera found at index {i}.")
        cap.release()
