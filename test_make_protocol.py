"""Basic smoke tests for make_protocol_template_bitrix.py"""

import os
import tempfile
import unittest
from pathlib import Path

from make_protocol_template_bitrix import build_md, build_docx, _validate_output_path, Vars


class TestProtocolTemplateGenerator(unittest.TestCase):
    """Test suite for protocol template generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_md_basic(self):
        """Test that build_md generates valid Markdown."""
        result = build_md(rows=3)
        
        # Check basic structure
        self.assertIn("ПРОТОКОЛ РАЗНОГЛАСИЙ", result)
        self.assertIn("Таблица разногласий", result)
        self.assertIn("Подписи сторон", result)
        
        # Check that all 3 rows are present
        for i in range(1, 4):
            self.assertIn(f"{{UF_CRM__TBD__CLAUSE_{i}_NUMBER__}}", result)
            self.assertIn(f"{{UF_CRM__TBD__CLAUSE_{i}_BUYER_TEXT__}}", result)
            self.assertIn(f"{{UF_CRM__TBD__CLAUSE_{i}_SUPPLIER_TEXT__}}", result)

    def test_build_md_single_row(self):
        """Test build_md with single row."""
        result = build_md(rows=1)
        self.assertIn("{UF_CRM__TBD__CLAUSE_1_NUMBER__}", result)
        # Should not have clause 2
        self.assertNotIn("{UF_CRM__TBD__CLAUSE_2_NUMBER__}", result)

    def test_build_docx_creates_file(self):
        """Test that build_docx creates a valid file."""
        output_path = Path(self.temp_dir) / "test_output.docx"
        
        build_docx(rows=5, out_docx=output_path)
        
        # Check file was created
        self.assertTrue(output_path.exists())
        
        # Check file size is reasonable (not empty)
        self.assertGreater(output_path.stat().st_size, 100)

    def test_build_docx_creates_directory(self):
        """Test that build_docx creates parent directories."""
        output_path = Path(self.temp_dir) / "subdir" / "nested" / "test.docx"
        
        build_docx(rows=2, out_docx=output_path)
        
        # Check file and directories were created
        self.assertTrue(output_path.exists())
        self.assertTrue(output_path.parent.exists())

    def test_validate_output_path_accepts_valid_paths(self):
        """Test that valid paths are accepted."""
        valid_path = Path(self.temp_dir) / "valid.docx"
        
        # Should not raise exception
        try:
            _validate_output_path(valid_path, "DOCX")
        except ValueError:
            self.fail("_validate_output_path raised ValueError for valid path")

    def test_validate_output_path_warns_on_traversal(self):
        """Test that path traversal triggers warning (but doesn't block)."""
        traversal_path = Path("../test.docx")
        
        # Should not raise exception (we only warn)
        try:
            _validate_output_path(traversal_path, "DOCX")
        except ValueError:
            self.fail("_validate_output_path raised ValueError unexpectedly")

    def test_vars_dataclass(self):
        """Test that Vars dataclass is properly configured."""
        v = Vars()
        
        # Check some key fields
        self.assertEqual(v.DOC_NUMBER, "{DocumentNumber}")
        self.assertEqual(v.SUPPLIER_NAME, "{MyCompanyRequisiteRqCompanyName}")
        self.assertEqual(v.BUYER_NAME, "{RequisiteRqCompanyName}")
        
        # Check that it's frozen (immutable)
        with self.assertRaises(Exception):  # FrozenInstanceError
            v.DOC_NUMBER = "test"

    def test_markdown_table_structure(self):
        """Test that Markdown table has correct structure."""
        result = build_md(rows=2)
        
        # Check table header
        self.assertIn("| Пункт договора | Редакция Покупателя | Редакция Поставщика | Согласованная редакция |", result)
        self.assertIn("|---|---|---|---|", result)


if __name__ == "__main__":
    unittest.main()
