import unittest
from util.utils import transform_response_content


class TestTransformResponseContent(unittest.TestCase):
    def test_short_string(self):
        content = "hello world"
        result = transform_response_content(content, chunk_size=5)
        self.assertEqual(result, ["hello", " worl", "d"])

    def test_exact_chunk(self):
        content = "abcdefghij"
        result = transform_response_content(content, chunk_size=5)
        self.assertEqual(result, ["abcde", "fghij"])

    def test_empty_string(self):
        content = ""
        result = transform_response_content(content, chunk_size=5)
        self.assertEqual(result, [])

    def test_chunk_larger_than_content(self):
        content = "abc"
        result = transform_response_content(content, chunk_size=10)
        self.assertEqual(result, ["abc"])


if __name__ == "__main__":
    unittest.main()
