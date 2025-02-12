import unittest
import json
from build_faiss_index import extract_filtered_tags

class TestExtractFilteredTags(unittest.TestCase):

    def test_empty_input(self):
        # Test that empty or None input returns an empty string.
        self.assertEqual(extract_filtered_tags(""), "")
        self.assertEqual(extract_filtered_tags(None), "")

    def test_valid_tags_above_threshold(self):
        # Input with three tags, one of which doesn't meet the threshold.
        tags_json = json.dumps([
            {"name": "isekai", "importance": 80},
            {"name": "magic", "importance": 70},
            {"name": "comedy", "importance": 50}
        ])
        # With threshold=60, only "isekai" and "magic" should be returned.
        result = extract_filtered_tags(tags_json, threshold=60)
        self.assertEqual(result, "isekai magic")  # Sorted alphabetically

    def test_all_tags_meet_threshold(self):
        tags_json = json.dumps([
            {"name": "isekai", "importance": 80},
            {"name": "magic", "importance": 70}
        ])
        result = extract_filtered_tags(tags_json, threshold=60)
        self.assertEqual(result, "isekai magic")

    def test_duplicate_tags(self):
        # Duplicate tags should be collapsed.
        tags_json = json.dumps([
            {"name": "isekai", "importance": 80},
            {"name": "isekai", "importance": 90}
        ])
        result = extract_filtered_tags(tags_json, threshold=60)
        self.assertEqual(result, "isekai")

    def test_no_tags_meet_threshold(self):
        # None of the tags meet the threshold.
        tags_json = json.dumps([
            {"name": "isekai", "importance": 40},
            {"name": "magic", "importance": 50}
        ])
        result = extract_filtered_tags(tags_json, threshold=60)
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()