import cv2
import mediapipe as mp
import numpy as np
import time
from dataclasses import dataclass
from typing import Tuple, List, Optional

@dataclass(frozen=True)
class AppConfig:
    WINDOW_NAME: str = "Identity Protection Cam"
    CAMERA_INDEX: int = 0
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    
    MODEL_SELECTION: int = 0 
    MIN_CONFIDENCE: float = 0.5
    
    COLOR_PRIMARY: Tuple[int, int, int] = (0, 255, 0)     
    COLOR_DIM: Tuple[int, int, int] = (0, 150, 0)         
    FONT: int = cv2.FONT_HERSHEY_SIMPLEX
    BLUR_KERNEL: Tuple[int, int] = (99, 99)
    BLUR_SIGMA: int = 30

class FaceDetector:
    
    def __init__(self, config: AppConfig):
        self.mp_face_detection = mp.solutions.face_detection
        self.detector = self.mp_face_detection.FaceDetection(
            model_selection=config.MODEL_SELECTION,
            min_detection_confidence=config.MIN_CONFIDENCE
        )

    def detect(self, image_rgb: np.ndarray) -> Optional[object]:
        return self.detector.process(image_rgb)

    def normalize_coordinates(self, detection, width: int, height: int) -> Tuple[int, int, int, int]:
        bboxC = detection.location_data.relative_bounding_box
        
        x = int(bboxC.xmin * width)
        y = int(bboxC.ymin * height)
        w = int(bboxC.width * width)
        h = int(bboxC.height * height)

        x = max(0, x)
        y = max(0, y)
        w = min(width - x, w)
        h = min(height - y, h)
        
        return x, y, w, h

class ImageProcessor:
    
    @staticmethod
    def apply_gaussian_blur(image: np.ndarray, roi: Tuple[int, int, int, int], config: AppConfig) -> np.ndarray:
        x, y, w, h = roi
        if w <= 0 or h <= 0: return image
        
        sub_face = image[y:y+h, x:x+w]
        blurred = cv2.GaussianBlur(sub_face, config.BLUR_KERNEL, config.BLUR_SIGMA)
        image[y:y+h, x:x+w] = blurred
        return image

    @staticmethod
    def apply_cyber_filter(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        zeros = np.zeros_like(gray)
        return cv2.merge([zeros, gray, zeros])

class HUDRenderer:
    
    def __init__(self, config: AppConfig):
        self.cfg = config

    def draw_interface(self, frame: np.ndarray) -> None:
        cv2.putText(frame, "AI FACE BLUR DETECTION", (20, 40), 
                    self.cfg.FONT, 0.7, self.cfg.COLOR_PRIMARY, 2, cv2.LINE_AA)
        
        curr_time = time.strftime("%H:%M:%S")
        status_text = f"SYSTEM: ONLINE | BUFFER: {curr_time}"
        cv2.putText(frame, status_text, (20, 70), 
                    self.cfg.FONT, 0.4, self.cfg.COLOR_DIM, 1, cv2.LINE_AA)

    def draw_detection_box(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> None:
        x, y, w, h = bbox
        line_len = int(w / 4)
        thickness = 2
        color = self.cfg.COLOR_PRIMARY

        cv2.line(frame, (x, y), (x + line_len, y), color, thickness)
        cv2.line(frame, (x, y), (x, y + line_len), color, thickness)
        
        cv2.line(frame, (x + w, y + h), (x + w - line_len, y + h), color, thickness)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - line_len), color, thickness)

        cv2.putText(frame, "IDENTITY HIDDEN", (x, y + h + 20), 
                    self.cfg.FONT, 0.4, color, 1, cv2.LINE_AA)

class CyberProtectionApp:
    
    def __init__(self):
        self.config = AppConfig()
        self.detector = FaceDetector(self.config)
        self.renderer = HUDRenderer(self.config)
        self.cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
        
        self._setup_camera()
        
    def _setup_camera(self):
        if not self.cap.isOpened():
            raise RuntimeError("CRITICAL: Camera access denied or hardware not found.")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        print(f"[INIT] Camera setup complete. Resolution: {self.config.FRAME_WIDTH}x{self.config.FRAME_HEIGHT}")

    def run(self):
        print("[SYSTEM] Starting surveillance stream...")
        try:
            while True:
                success, frame = self.cap.read()
                if not success:
                    print("[WARN] Dropped frame or stream ended.")
                    break

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.detector.detect(frame_rgb)
                
                h, w, _ = frame.shape
                detected_faces = []

                if results.detections:
                    for detection in results.detections:
                        bbox = self.detector.normalize_coordinates(detection, w, h)
                        detected_faces.append(bbox)
                        
                        ImageProcessor.apply_gaussian_blur(frame, bbox, self.config)

                cyber_frame = ImageProcessor.apply_cyber_filter(frame)

                self.renderer.draw_interface(cyber_frame)
                
                for bbox in detected_faces:
                    self.renderer.draw_detection_box(cyber_frame, bbox)

                cv2.imshow(self.config.WINDOW_NAME, cyber_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\n[SYSTEM] Force quit detected.")
        finally:
            self.cleanup()

    def cleanup(self):
        print("[SYSTEM] Releasing resources...")
        self.cap.release()
        cv2.destroyAllWindows()
        print("[SYSTEM] Shutdown complete.")

if __name__ == "__main__":
    app = CyberProtectionApp()
    app.run()