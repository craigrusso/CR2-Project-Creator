#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test Binary File Embedding

Tests for embedding binary files in structure JSON files.
"""

import os
import sys
import tempfile
import shutil
import unittest
import json
import base64

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import BinaryFileHandler directly (avoid circular imports)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'utils'))
from binary_file_handler import BinaryFileHandler

class TestBinaryFileHandler(unittest.TestCase):
    """Test the BinaryFileHandler utility"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test image file
        self.test_image_path = os.path.join(self.temp_dir, 'test_image.png')
        self._create_test_image()
        
        print(f"Test directory: {self.temp_dir}")
        print(f"Test image: {self.test_image_path}")
    
    def tearDown(self):
        """Clean up after tests"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_image(self):
        """Create a simple test PNG image"""
        # Create a small PNG file (1x1 pixel, red)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        
        with open(self.test_image_path, 'wb') as f:
            f.write(png_data)
    
    def test_is_binary_file(self):
        """Test binary file detection"""
        # Create a text file
        text_file_path = os.path.join(self.temp_dir, 'test.txt')
        with open(text_file_path, 'w') as f:
            f.write("This is a test text file")
        
        # Test detection
        self.assertTrue(BinaryFileHandler.is_binary_file(self.test_image_path))
        self.assertFalse(BinaryFileHandler.is_binary_file(text_file_path))
        
        print("Binary file detection works correctly")
    
    def test_should_embed_binary_file(self):
        """Test binary file size check for embedding decision"""
        # Create a large binary file
        large_file_path = os.path.join(self.temp_dir, 'large.bin')
        with open(large_file_path, 'wb') as f:
            f.write(os.urandom(1024 * 600))  # 600KB file
        
        # Test size checks
        self.assertTrue(BinaryFileHandler.should_embed_binary_file(self.test_image_path))
        self.assertFalse(BinaryFileHandler.should_embed_binary_file(large_file_path))
        self.assertTrue(BinaryFileHandler.should_embed_binary_file(large_file_path, max_size_kb=700))
        
        print("Binary file size check works correctly")
    
    def test_encode_decode_binary_file(self):
        """Test encoding and decoding binary files"""
        # Encode the test image
        encoded_data = BinaryFileHandler.encode_binary_file(self.test_image_path)
        
        # Verify encoding worked
        self.assertIsNotNone(encoded_data)
        self.assertTrue(len(encoded_data) > 0)
        
        # Decode to a new file
        decoded_path = os.path.join(self.temp_dir, 'decoded.png')
        success = BinaryFileHandler.decode_binary_file(encoded_data, decoded_path)
        
        # Verify decoding worked
        self.assertTrue(success)
        self.assertTrue(os.path.exists(decoded_path))
        
        # Check file sizes match
        original_size = os.path.getsize(self.test_image_path)
        decoded_size = os.path.getsize(decoded_path)
        self.assertEqual(original_size, decoded_size)
        
        print(f"Encoded data length: {len(encoded_data)}")
        print(f"Original size: {original_size}, Decoded size: {decoded_size}")
    
    def test_structure_json_simulation(self):
        """Test simulating structure JSON with embedded binary file"""
        # Encode the test image
        encoded_data = BinaryFileHandler.encode_binary_file(self.test_image_path)
        
        # Create a structure with embedded binary file
        structure = {
            "name": "TestStructure",
            "directories": [
                {"images": [
                    {
                        "type": "file",
                        "name": "embedded_image.png",
                        "is_binary": True,
                        "data": encoded_data
                    }
                ]},
                "README.txt"
            ]
        }
        
        # Save structure to JSON file
        structure_path = os.path.join(self.temp_dir, 'structure.json')
        with open(structure_path, 'w') as f:
            json.dump(structure, f, indent=2)
        
        # Verify JSON file can be read back
        with open(structure_path, 'r') as f:
            loaded_structure = json.load(f)
        
        # Verify structure is correct
        self.assertEqual(loaded_structure['name'], "TestStructure")
        self.assertIn('directories', loaded_structure)
        
        # Extract binary data
        binary_data = loaded_structure['directories'][0]['images'][0]['data']
        
        # Verify binary data matches
        self.assertEqual(binary_data, encoded_data)
        
        # Create a new file from the loaded data
        extracted_path = os.path.join(self.temp_dir, 'extracted.png')
        success = BinaryFileHandler.decode_binary_file(binary_data, extracted_path)
        
        # Verify extraction worked
        self.assertTrue(success)
        self.assertTrue(os.path.exists(extracted_path))
        
        # Check file sizes match
        original_size = os.path.getsize(self.test_image_path)
        extracted_size = os.path.getsize(extracted_path)
        self.assertEqual(original_size, extracted_size)
        
        print("Successfully simulated structure JSON with embedded binary file")

if __name__ == '__main__':
    unittest.main() 