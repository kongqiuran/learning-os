import unittest

from src.ai.utils.json_parser import LLMJSONParseError, parse_llm_json


class LLMJSONParserTest(unittest.TestCase):
    def test_parses_valid_json(self):
        self.assertEqual(parse_llm_json('{"name": "test"}'), {"name": "test"})

    def test_extracts_json_from_markdown_code_block(self):
        response = """```json
        {"name": "test", "items": [1, 2]}
        ```"""
        self.assertEqual(
            parse_llm_json(response),
            {"name": "test", "items": [1, 2]},
        )

    def test_repairs_literal_newline_inside_string(self):
        response = '{"summary": "hello\nworld"}'
        self.assertEqual(parse_llm_json(response)["summary"], "hello\nworld")

    def test_removes_trailing_commas(self):
        response = '{"name": "test", "items": [1, 2,],}'
        self.assertEqual(
            parse_llm_json(response),
            {"name": "test", "items": [1, 2]},
        )

    def test_repairs_single_quotes(self):
        response = "{'name': 'test', 'items': [1, 2,],}"
        self.assertEqual(
            parse_llm_json(response),
            {"name": "test", "items": [1, 2]},
        )

    def test_extracts_json_surrounded_by_plain_text(self):
        response = 'Here is the result:\n{"name": "test"}\nI hope this helps.'
        self.assertEqual(parse_llm_json(response), {"name": "test"})

    def test_closes_unterminated_brackets(self):
        response = '{"name": "test", "items": [1, 2'
        self.assertEqual(
            parse_llm_json(response),
            {"name": "test", "items": [1, 2]},
        )

    def test_rejects_response_without_json(self):
        with self.assertRaises(LLMJSONParseError):
            parse_llm_json("There is no structured result here.")


if __name__ == "__main__":
    unittest.main()
