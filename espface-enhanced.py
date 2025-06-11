import face_recognition
import cv2
import numpy as np
import time
import pickle
import serial
import sys
from datetime import datetime
from email_alert import send_email
import requests
from pathlib import Path

#receiver_email = "aditishastri.is23@rvce.edu.in"
#receiver_email = "aadityasrao.is23@rvce.edu.in"
receiver_email = "stopspammingaditi@gmail.com"

# Load encodings
print("[INFO] Loading encodings...")

def log_event(event_type, status, image_name=""):
    try:
        requests.post("http://127.0.0.1:5000/log", json={
            "type": event_type,
            "status": status,
            "image": image_name
        })
    except Exception as e:
        print(f"[LOG ERROR] Could not log event: {e}")

def save_intruder_image(frame):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    image_name = f"{timestamp}.jpg"
    path = Path("static/images")
    path.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path / image_name), frame)
    return image_name

try:
    with open("encodings.pickle", "rb") as f:
        data = pickle.loads(f.read())
    known_face_encodings = data["encodings"]
    known_face_names = data["names"]
    print(f"[INFO] Loaded {len(known_face_names)} known faces.")
except Exception as e:
    print(f"[ERROR] Failed to load encodings: {e}")
    sys.exit()

# Setup serial
try:
    ser = serial.Serial('COM6', 115200, timeout=10)
    time.sleep(1)
    ser.flushInput()
    print("[INFO] Connected to ESP32 on COM6.")
except serial.SerialException as e:
    print(f"[ERROR] Serial connection failed: {e}")
    sys.exit()

# Setup webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Could not open webcam.")
    sys.exit()
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("[INFO] Ready. Waiting for 'face_req'...")

while True:
    try:
        line = ser.readline().decode().strip()

        if line == "fp_match":
            print("[ESP] Fingerprint matched. Motor will run.")
            log_event("Fingerprint", "Success")
        elif line == "fp_fail":
            print("[ESP] Fingerprint failed.")
            log_event("Fingerprint", "Fail")

        elif line == "face_req":
            print("[INFO] 'face_req' received. Starting recognition.")

            start_time = time.time()
            timeout = 10
            match_found = False

            while time.time() - start_time < timeout:
                ret, frame = cap.read()
                if not ret:
                    print("[WARN] Frame not captured.")
                    continue

                cv2.imshow("Face Recognition - Press Q to cancel", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("[INFO] User cancelled.")
                    cv2.destroyAllWindows()

                    break

                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(rgb_small_frame, model="cnn")
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            print(f"[INFO] Face matched: {name}")
                            ser.write(b"face_match\n")
                            log_event("Face Recognition", "Success")
                            match_found = True
                            break
                if match_found:
                    break

            if not match_found:
                image_name = save_intruder_image(frame)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                subject = f"⚠️ Intruder Alert - {timestamp}"
                print("[INFO] No match found.")
                ser.write(b"face_fail\n")
                log_event("Face Recognition", "Fail", image_name)
                send_email(receiver_email, subject, "Fingerprint and face both failed.", frame)

            print("[INFO] Waiting for next 'face_req'...")

    except KeyboardInterrupt:
        ser.write(b"face_fail\n")
        ser.write(b"end_program\n")
        print("\n[INFO] Exiting by user.")
        cap.release()
        cv2.destroyAllWindows()
        break
    except Exception as e:
        print(f"[ERROR] {e}")
        if ser and ser.is_open:
            ser.write(b"face_fail\n")

# Final cleanup
cap.release()
cv2.destroyAllWindows()
