import os
import glob
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from utils.logger import logger

class DataManager:
    """
    Handles dataset scanning, validation, and statistics.
    Supports LabelMe JSON, VOC XML, and YOLO TXT formats.
    """
    
    SUPPORTED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
    SUPPORTED_ANNOTATION_EXTS = {'.json', '.xml', '.txt'}

    def __init__(self):
        self.dataset_path = None
        self.image_files = []
        self.annotation_files = []
        self.stats = {
            "total_images": 0,
            "total_annotations": 0,
            "classes": Counter(),
            "missing_annotations": 0
        }

    def scan_directory(self, path):
        """
        Scans the directory for images and annotations.
        Updates internal state and returns statistics.
        """
        self.dataset_path = Path(path)
        if not self.dataset_path.exists():
            logger.error(f"Dataset path does not exist: {path}")
            return None

        self._reset_stats()
        
        # Scan images
        unique_images = set()
        for ext in self.SUPPORTED_IMAGE_EXTS:
            unique_images.update(self.dataset_path.glob(f"*{ext}"))
            unique_images.update(self.dataset_path.glob(f"*{ext.upper()}"))
        
        self.image_files = sorted(list(unique_images))
        self.stats["total_images"] = len(self.image_files)
        
        # Scan annotations and validate pairing
        for img_path in self.image_files:
            stem = img_path.stem
            
            # Check for corresponding annotation file
            found_annotation = False
            for ext in self.SUPPORTED_ANNOTATION_EXTS:
                ann_path = self.dataset_path / (stem + ext)
                if ann_path.exists():
                    self.annotation_files.append(ann_path)
                    self._parse_annotation(ann_path)
                    found_annotation = True
                    break # Assume one annotation format per image
            
            if not found_annotation:
                self.stats["missing_annotations"] += 1

        self.stats["total_annotations"] = len(self.annotation_files)
        
        logger.info(f"Scanned dataset at {path}: {self.stats}")
        return self.stats

    def _reset_stats(self):
        self.image_files = []
        self.annotation_files = []
        self.stats = {
            "total_images": 0,
            "total_annotations": 0,
            "classes": Counter(),
            "missing_annotations": 0
        }

    def _parse_annotation(self, ann_path):
        """
        Parses annotation file to extract class labels.
        Supports: LabelMe JSON, VOC XML.
        YOLO TXT parsing requires a classes.txt file, which is handled separately.
        """
        try:
            suffix = ann_path.suffix.lower()
            if suffix == '.json':
                with open(ann_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for shape in data.get('shapes', []):
                        label = shape.get('label')
                        if label:
                            self.stats["classes"][label] += 1
            
            elif suffix == '.xml':
                tree = ET.parse(ann_path)
                root = tree.getroot()
                for obj in root.findall('object'):
                    name = obj.find('name').text
                    if name:
                        self.stats["classes"][name] += 1
            
            elif suffix == '.txt':
                # For YOLO, we just count lines as objects if we don't have classes.txt yet
                # Or we can try to read the class ID.
                # Here we simply increment a generic counter or skip specific class names 
                # until classes.txt is loaded.
                # For now, let's just count the number of lines.
                with open(ann_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip():
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                class_id = parts[0]
                                self.stats["classes"][f"class_{class_id}"] += 1

        except Exception as e:
            logger.warning(f"Failed to parse annotation {ann_path}: {e}")

    def get_classes(self):
        return list(self.stats["classes"].keys())

    def validate_dataset(self):
        """
        Performs validation checks.
        Returns a list of warnings/errors.
        """
        issues = []
        if self.stats["total_images"] == 0:
            issues.append("未找到任何图像文件。")
        
        if self.stats["total_annotations"] == 0:
            issues.append("未找到任何标注文件。")
            
        if self.stats["missing_annotations"] > 0:
            issues.append(f"有 {self.stats['missing_annotations']} 张图片缺少对应的标注文件。")
            
        return issues
