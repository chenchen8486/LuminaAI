import os
import cv2
import glob
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import numpy as np
from ultralytics import YOLO

@dataclass
class DetectionResult:
    """
    Result for a single detection/instance.
    """
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    mask: Optional[np.ndarray] = None  # Binary mask for segmentation

@dataclass
class ImageInferenceResult:
    """
    Inference result for a single image.
    """
    image_path: str
    detections: List[DetectionResult] = field(default_factory=list)
    original_shape: Tuple[int, int] = (0, 0)
    inference_time_ms: float = 0.0

class BatchInferenceEngine:
    """
    Engine for running batch inference on a directory of images using a trained YOLO model.
    """
    def __init__(self, model_path: str, device: str = 'cpu', conf_thres: float = 0.25, iou_thres: float = 0.45):
        """
        Initialize the inference engine.
        :param model_path: Path to the .pt model file.
        :param device: 'cpu' or 'cuda:0' (or verify availability).
        :param conf_thres: Confidence threshold for detection.
        :param iou_thres: IoU threshold for NMS.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        self.model_path = model_path
        self.device = device
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.model = None

    def load_model(self):
        """
        Lazy loading of the model.
        """
        if self.model is None:
            print(f"Loading model from {self.model_path} on {self.device}...")
            self.model = YOLO(self.model_path)
            # Warmup run? Not strictly necessary for batch inference unless time critical.

    def get_class_names(self) -> Dict[int, str]:
        self.load_model()
        return self.model.names

    def run_inference(self, image_dir: str, extensions: List[str] = ['*.jpg', '*.png', '*.jpeg']) -> List[ImageInferenceResult]:
        """
        Run inference on all images in the directory.
        Returns a list of ImageInferenceResult.
        """
        self.load_model()
        
        results_list = []
        image_files = []
        for ext in extensions:
            image_files.extend(glob.glob(os.path.join(image_dir, ext)))
        
        if not image_files:
            print(f"No images found in {image_dir}")
            return []

        # Predict using ultralytics
        # stream=True returns a generator, which is memory efficient for large batches
        results = self.model.predict(
            source=image_files, 
            device=self.device,
            conf=self.conf_thres,
            iou=self.iou_thres,
            stream=True,
            save=False,  # We handle saving visualization manually if needed
            verbose=False
        )

        for result in results:
            img_path = result.path
            orig_shape = result.orig_shape  # (h, w)
            inference_time = sum(result.speed.values()) # Preprocess + Inference + Postprocess

            detections = []
            if result.boxes:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    cls_name = self.model.names[cls_id]
                    
                    mask = None
                    if result.masks:
                        # Extract mask corresponding to this box?
                        # Ultralytics results structure: result.masks.data contains masks
                        # But mapping boxes to masks is done via index if sorted correctly.
                        # Usually, len(result.boxes) == len(result.masks)
                        # We need to find the mask corresponding to this detection.
                        # The masks are ordered same as boxes.
                        # However, iterating directly is safer.
                        pass # Implementing mask extraction requires careful index matching.
                    
                    detections.append(DetectionResult(
                        class_id=cls_id,
                        class_name=cls_name,
                        confidence=conf,
                        bbox=xyxy
                    ))
            
            # Handling masks if segmentation
            if result.masks:
                # Iterate again to attach masks properly? 
                # Or just assume order is preserved.
                # result.masks.xy contains polygon coordinates.
                # result.masks.data contains binary masks (on GPU usually).
                pass

            results_list.append(ImageInferenceResult(
                image_path=img_path,
                detections=detections,
                original_shape=orig_shape,
                inference_time_ms=inference_time
            ))
            
        return results_list

    def visualize_result(self, result: ImageInferenceResult, save_dir: str = None) -> np.ndarray:
        """
        Visualize the detection results on the image.
        Returns the annotated image (BGR format).
        """
        img = cv2.imread(result.image_path)
        if img is None:
            return None

        for det in result.detections:
            x1, y1, x2, y2 = map(int, det.bbox)
            label = f"{det.class_name} {det.confidence:.2f}"
            
            # Draw BBox
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw Label
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), (0, 255, 0), -1)
            cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Draw Mask if available (TODO)

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            filename = os.path.basename(result.image_path)
            save_path = os.path.join(save_dir, filename)
            cv2.imwrite(save_path, img)
            
        return img
