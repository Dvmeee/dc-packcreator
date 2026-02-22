"""Tests for src/packcreator.py"""

import os
import zipfile
import tempfile
import unittest

from src.packcreator import create_pack


class TestCreatePack(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory that acts as the source folder
        self.tmp = tempfile.TemporaryDirectory()
        self.source_dir = self.tmp.name
        self.output_dir = os.path.join(self.source_dir, "output")

        # Populate source with a couple of test files
        with open(os.path.join(self.source_dir, "file1.txt"), "w") as f:
            f.write("hello")
        sub = os.path.join(self.source_dir, "subdir")
        os.makedirs(sub)
        with open(os.path.join(sub, "file2.txt"), "w") as f:
            f.write("world")

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_zip_file(self):
        pack_path = create_pack(self.source_dir, self.output_dir, pack_name="testpack")
        self.assertTrue(os.path.isfile(pack_path))
        self.assertTrue(pack_path.endswith(".zip"))

    def test_zip_contains_expected_files(self):
        pack_path = create_pack(self.source_dir, self.output_dir, pack_name="testpack")
        with zipfile.ZipFile(pack_path, "r") as zf:
            names = zf.namelist()
        self.assertIn("file1.txt", names)
        self.assertIn("subdir/file2.txt", names)

    def test_default_name_uses_timestamp(self):
        pack_path = create_pack(self.source_dir, self.output_dir)
        self.assertTrue(os.path.isfile(pack_path))

    def test_raises_when_source_missing(self):
        with self.assertRaises(FileNotFoundError):
            create_pack("/nonexistent/path", self.output_dir)

    def test_raises_when_source_is_file(self):
        file_path = os.path.join(self.source_dir, "file1.txt")
        with self.assertRaises(NotADirectoryError):
            create_pack(file_path, self.output_dir)


if __name__ == "__main__":
    unittest.main()
