import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from collections import deque
import queue

class RealTimeGarbageDetector:
    def _init_(self, model_path='yolov8n.pt', confidence_threshold=0.5):
        # Load YOLOv8 model
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        
        # Garbage categories grouped from COCO classes (0-indexed)
        self.garbage_groups = {
            "Plastic Waste": {
                39: 'bottle',
                41: 'cup',
                42: 'fork',
                43: 'knife',
                44: 'spoon',
                45: 'bowl',
                24: 'backpack',
                26: 'handbag',
            },
            "Food Waste": {
                46: 'banana',
                47: 'apple',
                48: 'sandwich',
                49: 'orange',
                50: 'broccoli',
                51: 'carrot',
                52: 'hot dog',
                53: 'pizza',
                54: 'donut',
                55: 'cake',
            },
            "E-Waste": {
                62: 'tv',
                63: 'laptop',
                64: 'mouse',
                65: 'remote',
                66: 'keyboard',
                67: 'cell phone',
                68: 'microwave',
                69: 'oven',
                70: 'toaster',
                71: 'sink',
                72: 'refrigerator',
            },
            "Furniture Waste": {
                56: 'chair',
                57: 'couch',
                58: 'potted plant',
            },
            "Paper/Glass Waste": {
                73: 'book',
                75: 'vase',
                40: 'wine glass',
            },
            "Sanitary/Other Waste": {
                61: 'toilet',
                25: 'umbrella',
                27: 'tie',
                28: 'suitcase',
                76: 'scissors',
                79: 'toothbrush',
            }
        }

        # Flatten into a single mapping (class_id → category, name)
        self.garbage_classes = {}
        for category, items in self.garbage_groups.items():
            for cid, cname in items.items():
                self.garbage_classes[cid] = (category, cname)
        
        # Performance optimization
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=2)
        self.running = False
        
        # FPS tracking
        self.fps_counter = deque(maxlen=30)
        self.last_time = time.time()
        
    def preprocess_frame(self, frame):
        """Optimize frame for faster processing"""
        height, width = frame.shape[:2]
        if width > 640:
            scale = 640 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        return frame
    
    def detect_garbage(self, frame):
        """Detect garbage objects in frame"""
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in self.garbage_classes:
                        category, class_name = self.garbage_classes[class_id]
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        detection = {
                            'class_id': class_id,
                            'class_name': class_name,
                            'category': category,
                            'confidence': confidence,
                            'bbox': [int(x1), int(y1), int(x2), int(y2)]
                        }
                        detections.append(detection)
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on frame"""
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class_name']
            category = detection['category']
            confidence = detection['confidence']
            
            # Draw bounding box
            color = (0, 255, 0)  # Green for garbage detection
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Label with class + category
            label = f"{class_name} ({category}): {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        return frame
    
    def calculate_fps(self):
        """Calculate and return current FPS"""
        current_time = time.time()
        self.fps_counter.append(1.0 / (current_time - self.last_time))
        self.last_time = current_time
        return sum(self.fps_counter) / len(self.fps_counter)
    
    def detection_worker(self):
        """Worker thread for running detections"""
        while self.running:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get_nowait()
                    detections = self.detect_garbage(frame)
                    
                    if not self.detection_queue.full():
                        self.detection_queue.put(detections)
                    else:
                        try:
                            self.detection_queue.get_nowait()
                            self.detection_queue.put(detections)
                        except queue.Empty:
                            pass
            except queue.Empty:
                time.sleep(0.001)
    
    def run_detection(self):
        """Main detection loop"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        self.running = True
        detection_thread = threading.Thread(target=self.detection_worker)
        detection_thread.daemon = True
        detection_thread.start()
        
        print("Garbage Detection Started! Press 'q' to quit, 's' to save frame.")
        latest_detections = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
            
            processed_frame = self.preprocess_frame(frame)
            
            if not self.frame_queue.full():
                self.frame_queue.put(processed_frame.copy())
            
            try:
                latest_detections = self.detection_queue.get_nowait()
            except queue.Empty:
                pass
            
            display_frame = self.draw_detections(frame.copy(), latest_detections)
            
            fps = self.calculate_fps()
            cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            garbage_count = len(latest_detections)
            cv2.putText(display_frame, f"Garbage Items: {garbage_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Optional: show grouped summary
            y_offset = 90
            categories_seen = {}
            for d in latest_detections:
                categories_seen[d['category']] = categories_seen.get(d['category'], 0) + 1
            for cat, count in categories_seen.items():
                cv2.putText(display_frame, f"{cat}: {count}", (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                y_offset += 25
            
            cv2.imshow('Real-time Garbage Detection', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                timestamp = int(time.time())
                filename = f"garbage_detection_{timestamp}.jpg"
                cv2.imwrite(filename, display_frame)
                print(f"Frame saved as {filename}")
        
        self.running = False
        cap.release()
        cv2.destroyAllWindows()
        print("Detection stopped")

    def run_on_image(self, image_path):
        """Run detection on a single image"""
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Error: Could not load image {image_path}")
            return
        
        detections = self.detect_garbage(frame)
        result_frame = self.draw_detections(frame, detections)
        
        print(f"Found {len(detections)} garbage items:")
        for detection in detections:
            print(f"- {detection['class_name']} ({detection['category']}): {detection['confidence']:.2f}")
        
        cv2.imshow('Garbage Detection Result', result_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# Usage example
if __name__ == "__main__":
    detector = RealTimeGarbageDetector(confidence_threshold=0.4)
    detector.run_detection()
    # detector.run_on_image("path_to_your_image.jpg")