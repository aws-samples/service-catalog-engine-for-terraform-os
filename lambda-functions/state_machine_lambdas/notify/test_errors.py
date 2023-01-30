from unittest import main, TestCase

from notify.errors import workflow_has_error, get_failure_reason

class TestErrors(TestCase):

    def test_workflow_has_error_with_no_error_present(self):
        self.assertFalse(workflow_has_error({'key': 'value'}))

    def test_workflow_has_error_with_error_present(self):
        event = {'error': 'SomeError', 'errorMessage': 'What happened?', 'key': 'value'}
        self.assertTrue(workflow_has_error(event))

    def test_get_failure_reason_happy_path(self):
        # Arrange
        event = {'error': 'SomeError', 'errorMessage': 'What happened?', 'key': 'value'}

        # Act
        actual = get_failure_reason(event)

        # Assert
        self.assertEqual(event['errorMessage'], actual)

    def test_get_failure_reason_lambda_timeout(self):
        # Arrange
        event = {'error': 'States.Timeout', 'errorMessage': 'What happened?', 'key': 'value'}
        expected_failure_reason = 'A lambda function invoked by the state machine has timed out'

        # Act
        actual = get_failure_reason(event)

        # Assert
        self.assertEqual(expected_failure_reason, actual)

    def test_get_failure_reason_with_very_long_error_message(self):
        # Arrange
        very_long_error_message = 'x' * 5000
        event = {'error': 'RuntimeError', 'errorMessage': very_long_error_message, 'key': 'value'}
        expected_failure_reason = 'x' * 2045 + '...'

        # Act
        actual = get_failure_reason(event)

        # Assert
        self.assertEqual(expected_failure_reason, actual)


if __name__ == '__main__':
    main()
