import os
import glob
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from core.inference.inference_engine import ImageInferenceResult, DetectionResult

@dataclass
class EvalMetrics:
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    tp: int = 0
    fp: int = 0
    fn: int = 0

@dataclass
class ClassMetrics:
    class_id: int
    class_name: str
    metrics: EvalMetrics

@dataclass
class EvaluationReport:
    overall_metrics: EvalMetrics
    class_metrics: Dict[int, ClassMetrics] = field(default_factory=dict)
    fp_images: List[str] = field(default_factory=list) # List of image paths with False Positives
    fn_images: List[str] = field(default_factory=list) # List of image paths with False Negatives

class Evaluator:
    """
    Evaluator for Object Detection.
    Calculates Precision, Recall, F1, and identifies FP/FN images.
    """
    def __init__(self, iou_threshold: float = 0.5):
        self.iou_threshold = iou_threshold

    def evaluate(self, predictions: List[ImageInferenceResult], gt_dir: str, class_names: Dict[int, str]) -> EvaluationReport:
        """
        Evaluate predictions against Ground Truth.
        Assumes GT files are in YOLO format (.txt) with same basename as images.
        """
        report = EvaluationReport(overall_metrics=EvalMetrics())
        
        # Aggregate counts
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        class_stats = {} # {class_id: {'tp': 0, 'fp': 0, 'fn': 0}}

        for pred_result in predictions:
            image_path = pred_result.image_path
            basename = os.path.splitext(os.path.basename(image_path))[0]
            txt_path = os.path.join(gt_dir, basename + ".txt")
            
            img_h, img_w = pred_result.original_shape
            
            gt_boxes = [] # List of [class_id, x1, y1, x2, y2]
            
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            cx, cy, w, h = map(float, parts[1:5])
                            
                            # Convert YOLO (norm) to xyxy (abs)
                            x1 = (cx - w/2) * img_w
                            y1 = (cy - h/2) * img_h
                            x2 = (cx + w/2) * img_w
                            y2 = (cy + h/2) * img_h
                            
                            gt_boxes.append({'class_id': cls_id, 'bbox': [x1, y1, x2, y2], 'matched': False})
            
            # Per image evaluation
            img_tp = 0
            img_fp = 0
            img_fn = 0
            
            # Sort predictions by confidence (descending)
            sorted_preds = sorted(pred_result.detections, key=lambda x: x.confidence, reverse=True)
            
            for pred in sorted_preds:
                pred_cls = pred.class_id
                pred_box = pred.bbox
                
                best_iou = 0
                best_gt_idx = -1
                
                # Find best matching GT
                for i, gt in enumerate(gt_boxes):
                    if gt['class_id'] == pred_cls and not gt['matched']:
                        iou = self._compute_iou(pred_box, gt['bbox'])
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = i
                
                if best_iou >= self.iou_threshold:
                    # TP
                    gt_boxes[best_gt_idx]['matched'] = True
                    img_tp += 1
                    self._update_class_stat(class_stats, pred_cls, 'tp')
                else:
                    # FP
                    img_fp += 1
                    self._update_class_stat(class_stats, pred_cls, 'fp')
            
            # Remaining unmatched GTs are FN
            for gt in gt_boxes:
                if not gt['matched']:
                    img_fn += 1
                    self._update_class_stat(class_stats, gt['class_id'], 'fn')
            
            total_tp += img_tp
            total_fp += img_fp
            total_fn += img_fn
            
            if img_fp > 0:
                report.fp_images.append(image_path)
            if img_fn > 0:
                report.fn_images.append(image_path)

        # Calculate Overall Metrics (Micro-average)
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        report.overall_metrics = EvalMetrics(precision, recall, f1, total_tp, total_fp, total_fn)
        
        # Calculate Per-Class Metrics
        for cls_id, stats in class_stats.items():
            tp = stats['tp']
            fp = stats['fp']
            fn = stats['fn']
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            f = 2 * (p * r) / (p + r) if (p + r) > 0 else 0
            
            cls_name = class_names.get(cls_id, str(cls_id))
            report.class_metrics[cls_id] = ClassMetrics(cls_id, cls_name, EvalMetrics(p, r, f, tp, fp, fn))
            
        return report

    def _update_class_stat(self, stats, cls_id, key):
        if cls_id not in stats:
            stats[cls_id] = {'tp': 0, 'fp': 0, 'fn': 0}
        stats[cls_id][key] += 1

    def _compute_iou(self, box1, box2):
        """
        Calculate IoU between two boxes [x1, y1, x2, y2]
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0
            
        return intersection / union
