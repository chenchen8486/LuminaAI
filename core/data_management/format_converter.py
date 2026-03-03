import json
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import cv2
from utils.logger import logger

class FormatConverter:
    """
    Handles conversion between different annotation formats.
    Supports:
    - LabelMe JSON -> VOC XML
    - LabelMe JSON -> YOLO TXT
    - LabelMe JSON -> Binary Mask
    """

    @staticmethod
    def json_to_xml(json_path, output_dir):
        """
        Converts LabelMe JSON to Pascal VOC XML.
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            img_path = data.get('imagePath')
            img_height = data.get('imageHeight')
            img_width = data.get('imageWidth')
            filename = Path(img_path).name
            
            root = ET.Element('annotation')
            ET.SubElement(root, 'folder').text = output_dir
            ET.SubElement(root, 'filename').text = filename
            ET.SubElement(root, 'path').text = str(Path(output_dir) / filename)
            
            source = ET.SubElement(root, 'source')
            ET.SubElement(source, 'database').text = 'Unknown'
            
            size = ET.SubElement(root, 'size')
            ET.SubElement(size, 'width').text = str(img_width)
            ET.SubElement(size, 'height').text = str(img_height)
            ET.SubElement(size, 'depth').text = '3' # Assuming RGB
            
            ET.SubElement(root, 'segmented').text = '0'
            
            for shape in data.get('shapes', []):
                label = shape.get('label')
                points = shape.get('points')
                shape_type = shape.get('shape_type')
                
                if shape_type == 'rectangle':
                    (x1, y1), (x2, y2) = points
                    xmin = min(x1, x2)
                    ymin = min(y1, y2)
                    xmax = max(x1, x2)
                    ymax = max(y1, y2)
                    
                    obj = ET.SubElement(root, 'object')
                    ET.SubElement(obj, 'name').text = label
                    ET.SubElement(obj, 'pose').text = 'Unspecified'
                    ET.SubElement(obj, 'truncated').text = '0'
                    ET.SubElement(obj, 'difficult').text = '0'
                    
                    bndbox = ET.SubElement(obj, 'bndbox')
                    ET.SubElement(bndbox, 'xmin').text = str(int(xmin))
                    ET.SubElement(bndbox, 'ymin').text = str(int(ymin))
                    ET.SubElement(bndbox, 'xmax').text = str(int(xmax))
                    ET.SubElement(bndbox, 'ymax').text = str(int(ymax))
            
            tree = ET.ElementTree(root)
            output_path = Path(output_dir) / (Path(json_path).stem + '.xml')
            tree.write(output_path, encoding='utf-8')
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert JSON to XML: {e}")
            return False

    @staticmethod
    def json_to_mask(json_path, output_dir, class_mapping=None):
        """
        Converts LabelMe JSON to Binary Mask (for Segmentation).
        class_mapping: dict {label_name: pixel_value}
        If class_mapping is None, it generates a binary mask (0: background, 255: foreground).
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            img_height = data.get('imageHeight')
            img_width = data.get('imageWidth')
            
            mask = np.zeros((img_height, img_width), dtype=np.uint8)
            
            for shape in data.get('shapes', []):
                label = shape.get('label')
                points = np.array(shape.get('points'), dtype=np.int32)
                shape_type = shape.get('shape_type')
                
                if shape_type == 'polygon' or shape_type == 'rectangle':
                    if class_mapping:
                        color = class_mapping.get(label, 0)
                    else:
                        color = 255
                        
                    cv2.fillPoly(mask, [points], color)
            
            output_path = Path(output_dir) / (Path(json_path).stem + '.png')
            cv2.imwrite(str(output_path), mask)
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert JSON to Mask: {e}")
            return False

    @staticmethod
    def json_to_yolo(json_path, output_dir, class_list):
        """
        Converts LabelMe JSON to YOLO TXT format.
        class_list: list of class names (index corresponds to class ID)
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            img_height = data.get('imageHeight')
            img_width = data.get('imageWidth')
            
            yolo_lines = []
            
            for shape in data.get('shapes', []):
                label = shape.get('label')
                if label not in class_list:
                    continue
                
                class_id = class_list.index(label)
                points = shape.get('points')
                shape_type = shape.get('shape_type')
                
                if shape_type == 'rectangle':
                    (x1, y1), (x2, y2) = points
                    xmin = min(x1, x2)
                    ymin = min(y1, y2)
                    xmax = max(x1, x2)
                    ymax = max(y1, y2)
                    
                    # Normalize coordinates
                    x_center = ((xmin + xmax) / 2) / img_width
                    y_center = ((ymin + ymax) / 2) / img_height
                    w = (xmax - xmin) / img_width
                    h = (ymax - ymin) / img_height
                    
                    yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
                
                elif shape_type == 'polygon':
                    # For segmentation (YOLOv8-Seg format): class_id x1 y1 x2 y2 ...
                    points_norm = []
                    for x, y in points:
                        points_norm.append(f"{x/img_width:.6f} {y/img_height:.6f}")
                    
                    line = f"{class_id} " + " ".join(points_norm)
                    yolo_lines.append(line)

            output_path = Path(output_dir) / (Path(json_path).stem + '.txt')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(yolo_lines))
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert JSON to YOLO: {e}")
            return False
