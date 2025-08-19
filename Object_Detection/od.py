# collector_bt.py
import time
import cv2
import serial
from ultralytics import YOLO

# ----- CONFIG -----
BT_PORT = "COM6"         # change to your Bluetooth COM port
BAUD    = 9600
MODEL   = "yolov8n.pt"   # small & fast
TARGETS = {"bottle", "cup", "plastic"}  # names you consider garbage (use model.names to check)
CONF_TH = 0.45
IMG_SZ  = 320
X_TOL   = 80             # horizontal tolerance in pixels to consider 'centered'
CENTER_WAIT = 3          # frames must be centered before moving forward
SEND_REPEAT_DELAY = 0.2  # seconds between repeated sends (avoid flooding)
# -------------------

# Connect to HC-05 Bluetooth COM port
print("Opening Bluetooth serial:", BT_PORT)
bt = serial.Serial(BT_PORT, BAUD, timeout=0.1)
time.sleep(2)  # allow connection to settle

# Load YOLO model
model = YOLO(MODEL)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise SystemExit("Cannot open webcam")

last_cmd = None
last_send_time = 0
centered_count = 0

print("Running. Press 'q' to quit.")
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]

        results = model(frame, conf=CONF_TH, imgsz=IMG_SZ, verbose=False)
        annotated = results[0].plot()  # annotated image

        # find best target
        target_box = None
        target_label = None
        best_conf = 0.0
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = model.names[cls_id]
            if label in TARGETS and conf > best_conf:
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                target_box = (x1, y1, x2, y2)
                best_conf = conf
                target_label = label

        cmd_to_send = 'S'  # default stop
        if target_box is not None:
            x1, y1, x2, y2 = target_box
            cx = (x1 + x2) // 2
            offset_x = cx - (w // 2)

            # draw center marker
            cv2.circle(annotated, (cx, (y1+y2)//2), 4, (0,0,255), -1)
            cv2.putText(annotated, f"{target_label} {best_conf:.2f}", (x1, y1-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            # steering logic
            if abs(offset_x) <= X_TOL:
                centered_count += 1
            else:
                centered_count = 0

            if abs(offset_x) > X_TOL:
                if offset_x < 0:
                    cmd_to_send = 'L'
                else:
                    cmd_to_send = 'R'
            else:
                # centered horizontally
                if centered_count >= CENTER_WAIT:
                    cmd_to_send = 'F'
                else:
                    cmd_to_send = 'S'
        else:
            centered_count = 0
            cmd_to_send = 'S'

        # Send command if changed or after repeat delay
        now = time.time()
        if cmd_to_send != last_cmd or (now - last_send_time) > SEND_REPEAT_DELAY:
            try:
                bt.write(cmd_to_send.encode())
                # debug print
                print("Sent:", cmd_to_send)
            except serial.SerialException as e:
                print("Serial write error:", e)
            last_cmd = cmd_to_send
            last_send_time = now

        # Read Arduino messages (e.g., 'D' when too close)
        try:
            if bt.in_waiting:
                line = bt.readline().decode().strip()
                if line:
                    print("From Arduino:", line)
                    if 'D' in line:
                        # stop and pick
                        bt.write(b'S')
                        time.sleep(0.2)
                        bt.write(b'P')  # pick command
                        print("Picking...")
                        time.sleep(1.0)
                        bt.write(b'O')  # open/release after
        except Exception as e:
            print("Serial read error:", e)

        # show annotated frame
        cv2.imshow("Collector (Bluetooth)", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    bt.close()
    cv2.destroyAllWindows()
    print("Stopped.")

