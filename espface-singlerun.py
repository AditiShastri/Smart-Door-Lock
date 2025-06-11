import face_recognition
import cv2
import numpy as np
import time
import pickle
import serial
import sys

# Load pre-trained face encodings
print("[INFO] Loading encodings...")
try:
    with open("encodings.pickle", "rb") as f:
        data = pickle.loads(f.read())
    known_face_encodings = data["encodings"]
    known_face_names = data["names"]
    print(f"[INFO] Loaded encodings for {len(known_face_names)} known faces.")
except FileNotFoundError:
    print("[ERROR] 'encodings.pickle' not found. Please run 'model_training.py' first.")
    exit()
except Exception as e:
    print(f"[ERROR] An error occurred while loading encodings: {e}")
    exit()

# --- Setup serial communication ---
#ESP is at COM6
try:
    ser = serial.Serial('COM6', 115200, timeout=10)  # CHANGE COM PORT as needed
    print("[INFO] Serial connection established with ESP32.")
except serial.SerialException as e:
    print(f"[ERROR] Could not open serial port: {e}")
    sys.exit()

# --- Wait for ESP32 request ---
print("[INFO] Waiting for 'face_req' signal from ESP32...")
while True:
    try:
        line = ser.readline().decode().strip()
        if line == "face_req":
            print("[INFO] Face recognition requested by ESP32.")
            break
    except Exception as e:
        print(f"[ERROR] Serial read error: {e}")
        ser.write(b"face_fail\n")
        sys.exit()

# --- Initialize webcam ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Could not open webcam.")
    ser.write(b"face_fail\n")
    sys.exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# --- Capture one frame ---
ret, frame = cap.read()
cap.release()
cv2.destroyAllWindows()

if not ret:
    print("[ERROR] Failed to grab frame.")
    ser.write(b"face_fail\n")
    sys.exit()

# --- Process the frame ---
cv_scaler = 4
resized_frame = cv2.resize(frame, (0, 0), fx=(1 / float(cv_scaler)), fy=(1 / float(cv_scaler)))
rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
face_locations = face_recognition.face_locations(rgb_resized_frame, model="hog")
face_encodings = face_recognition.face_encodings(rgb_resized_frame, face_locations)

face_names = []
for face_encoding in face_encodings:
    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
    name = "Unknown"
    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
    if len(face_distances) > 0:
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
    face_names.append(name)

# --- Decide and send result ---
match_found = any(name != "Unknown" for name in face_names)
if match_found:
    print("[INFO] Face matched. Sending 'face_match'")
    ser.write(b"face_match\n")
else:
    print("[INFO] Face not recognized. Sending 'face_fail'")
    ser.write(b"face_fail\n")

print("Application completed.")
sys.exit()
