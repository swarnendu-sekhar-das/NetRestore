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
            self.assertEqual(kwargs["input_dir"], temp_dir)
            self.assertEqual(kwargs["required_exts"], SOP_FILE_EXTENSIONS)
            self.assertEqual(SOP_FILE_EXTENSIONS, [".pdf"])

    def test_production_entry_points_target_sop_directory(self):
        with open("scripts/ingest_data.py") as script:
            self.assertIn("data/sops", script.read())
        with open("scripts/start.sh") as script:
            self.assertIn("/app/data/sops", script.read())
