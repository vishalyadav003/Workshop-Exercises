import unittest

from src.config import Settings, validate_settings


class ConfigTests(unittest.TestCase):
    def test_valid_settings_pass(self):
        settings = Settings("development", "demo", "local-test-token", "INFO")
        self.assertEqual(validate_settings(settings), [])

    def test_missing_token_fails_without_echoing_value(self):
        settings = Settings("development", "demo", "", "INFO")
        errors = validate_settings(settings)
        self.assertTrue(any("API_TOKEN" in error for error in errors))
        self.assertNotIn("secret", " ".join(errors).lower())

    def test_invalid_log_level_fails(self):
        settings = Settings("development", "demo", "local-token", "LOUD")
        self.assertTrue(any("LOG_LEVEL" in error for error in validate_settings(settings)))


if __name__ == "__main__":
    unittest.main()
