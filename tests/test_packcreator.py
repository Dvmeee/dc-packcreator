"""Tests for src/packcreator.py"""

import os
import zipfile
import tempfile
import unittest

from src.packcreator import create_carpack, create_pack


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


class TestCreateCarpack(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_dir = self.tmp.name
        self.output_dir = os.path.join(self.root_dir, "output")
        self.template_dir = os.path.join(self.root_dir, "xyz")

        self.vehicle_one = os.path.join(self.root_dir, "car_alpha")
        self.vehicle_two = os.path.join(self.root_dir, "car_beta")
        os.makedirs(self.vehicle_one)
        os.makedirs(self.vehicle_two)
        os.makedirs(self.template_dir)
        os.makedirs(os.path.join(self.template_dir, "audioconfig"))

        with open(os.path.join(self.template_dir, "fxmanifest.lua"), "w") as f:
            f.write("fx_version 'cerulean'\ngame 'gta5'\n")
        with open(os.path.join(self.template_dir, "audioconfig", "preset.dat54.rel"), "w") as f:
            f.write("audio")

        with open(os.path.join(self.vehicle_one, "vehicles.meta"), "w") as f:
            f.write("meta")
        with open(os.path.join(self.vehicle_one, "model.yft"), "w") as f:
            f.write("stream")

        with open(os.path.join(self.vehicle_two, "handling.meta"), "w") as f:
            f.write("meta")
        with open(os.path.join(self.vehicle_two, "anim.ycd"), "w") as f:
            f.write("stream")

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_carpack_zip(self):
        pack_path = create_carpack(
            [self.vehicle_one, self.vehicle_two],
            self.output_dir,
            pack_name="cars",
            template_dir=self.template_dir,
        )
        self.assertTrue(os.path.isfile(pack_path))
        self.assertTrue(pack_path.endswith(".zip"))

    def test_routes_meta_to_data_and_assets_to_stream(self):
        pack_path = create_carpack(
            [self.vehicle_one, self.vehicle_two],
            self.output_dir,
            pack_name="cars",
            template_dir=self.template_dir,
        )
        with zipfile.ZipFile(pack_path, "r") as zf:
            names = set(zf.namelist())

        self.assertIn("data/car_alpha/vehicles.meta", names)
        self.assertIn("data/car_beta/handling.meta", names)
        self.assertIn("stream/car_alpha/model.yft", names)
        self.assertIn("stream/car_beta/anim.ycd", names)

    def test_creates_required_pack_folders(self):
        pack_path = create_carpack(
            [self.vehicle_one],
            self.output_dir,
            pack_name="cars",
            template_dir=self.template_dir,
        )
        with zipfile.ZipFile(pack_path, "r") as zf:
            names = set(zf.namelist())

        self.assertIn("audioconfig/", names)
        self.assertIn("data/", names)
        self.assertIn("stream/", names)
        self.assertIn("sfx/", names)

    def test_raises_when_no_vehicle_folder_provided(self):
        with self.assertRaises(ValueError):
            create_carpack([], self.output_dir, template_dir=self.template_dir)

    def test_copies_fxmanifest_and_audioconfig_from_template(self):
        pack_path = create_carpack(
            [self.vehicle_one],
            self.output_dir,
            pack_name="cars",
            template_dir=self.template_dir,
        )
        with zipfile.ZipFile(pack_path, "r") as zf:
            names = set(zf.namelist())

        self.assertIn("fxmanifest.lua", names)
        self.assertIn("audioconfig/preset.dat54.rel", names)
