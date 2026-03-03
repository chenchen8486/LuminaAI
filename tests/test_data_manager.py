import unittest
import sys
import os
import shutil
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_management.data_manager import DataManager

class TestDataManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/temp_dummy_dataset")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True)
        
        # Create dummy data
        # Image 1: JSON
        (self.test_dir / "image1.jpg").touch()
        with open(self.test_dir / "image1.json", 'w') as f:
            json.dump({
                "shapes": [{"label": "cat", "points": [[10, 10], [50, 50]], "shape_type": "rectangle"}]
            }, f)
            
        # Image 2: XML
        (self.test_dir / "image2.png").touch()
        root = ET.Element('annotation')
        obj = ET.SubElement(root, 'object')
        ET.SubElement(obj, 'name').text = 'dog'
        tree = ET.ElementTree(root)
        tree.write(self.test_dir / "image2.xml")
        
        # Image 3: Missing
        (self.test_dir / "image3.jpg").touch()

        self.dm = DataManager()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_scan_directory(self):
        stats = self.dm.scan_directory(self.test_dir)
        
        self.assertEqual(stats["total_images"], 3)
        self.assertEqual(stats["total_annotations"], 2)
        self.assertEqual(stats["missing_annotations"], 1)
        self.assertEqual(stats["classes"]["cat"], 1)
        self.assertEqual(stats["classes"]["dog"], 1)

if __name__ == '__main__':
    unittest.main()