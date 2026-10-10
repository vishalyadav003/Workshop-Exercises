import unittest
from unittest.mock import patch

from src import validate_env


class EnvironmentAuditTests(unittest.TestCase):
    def test_audit_does_not_print_values_and_accepts_complete_environment(self):
        env = {"APP_ENV": "test", "APP_NAME": "demo", "API_TOKEN": "unit-test-token", "LOG_LEVEL": "INFO"}
        with patch.dict("os.environ", env, clear=True), patch.object(validate_env, "REQUIREMENTS") as req:
            req.is_file.return_value = True
            req.read_text.return_value = "python-dotenv==1.0.1\n"
            with patch.object(validate_env.importlib.metadata, "version", return_value="1.0.1"):
                self.assertEqual(validate_env.audit(), [])

    def test_missing_environment_names_are_reported_without_values(self):
        with patch.dict("os.environ", {}, clear=True), patch.object(validate_env, "REQUIREMENTS") as req, patch.object(validate_env, "ROOT") as root:
            req.is_file.return_value = True
            req.read_text.return_value = ""
            root.__truediv__.return_value.is_file.return_value = False
            errors = validate_env.audit()
        self.assertTrue(any("API_TOKEN" in error for error in errors))
        self.assertNotIn("unit-test-token", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
