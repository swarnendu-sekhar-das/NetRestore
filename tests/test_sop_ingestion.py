import os
import tempfile
import unittest
from unittest.mock import patch

from src.data_engineering.parser import SOP_FILE_EXTENSIONS, TelecomDocumentParser


class SopIngestionTests(unittest.TestCase):
    def test_parser_allow_lists_only_sop_pdfs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            open(os.path.join(temp_dir, "approved_sop.pdf"), "w").close()
            open(os.path.join(temp_dir, "network_topology.json"), "w").close()
            open(os.path.join(temp_dir, "evaluation_qa.json"), "w").close()

            with patch("src.data_engineering.parser.SimpleDirectoryReader") as reader:
                reader.return_value.load_data.return_value = []
                TelecomDocumentParser(temp_dir).load_documents()

            _, kwargs = reader.call_args
            self.assertIn("input_files", kwargs)
            self.assertEqual(len(kwargs["input_files"]), 1)
            self.assertTrue(kwargs["input_files"][0].endswith("approved_sop.pdf"))

    def test_production_entry_points_target_sop_directory(self):
        with open("scripts/ingest_data.py") as script:
            self.assertIn("data/sops", script.read())
