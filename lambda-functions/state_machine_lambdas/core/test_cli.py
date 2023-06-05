from unittest import main, TestCase

from core.cli import create_runuser_command_with_default_user, double_escape_double_quotes, double_escape_double_quotes_and_backslashes, triple_escape_double_single_quotes, escape_quotes_backslashes

class TestCli(TestCase):

    def test_create_runuser_command_with_default_user_happy_path(self):
        # Arrange
        base_command = 'base'
        expected = "runuser -l ec2-user -c 'base'"

        # Act
        actual = create_runuser_command_with_default_user(base_command)

        # Assert
        self.assertEqual(expected, actual)

    def test_create_runuser_command_with_default_user_base_command_is_empty(self):
        # Act
        with self.assertRaises(ValueError) as context:
            create_runuser_command_with_default_user('')

        # Assert
        self.assertEqual(context.expected, ValueError)
        self.assertEqual(str(context.exception), 'base_command must be a non-empty string')

    def test_create_runuser_command_with_default_user_base_command_is_None(self):
        # Act
        with self.assertRaises(ValueError) as context:
            create_runuser_command_with_default_user(None)

        # Assert
        self.assertEqual(context.expected, ValueError)
        self.assertEqual(str(context.exception), 'base_command must be a non-empty string')

    def test_double_escape_double_quotes_happy_path(self):
        # Arrange
        input = '"'
        expected = '\\"'

        # Act
        actual = double_escape_double_quotes(input)

        # Assert
        self.assertEqual(expected, actual)

    def test_double_escape_double_quotes_input_is_empty(self):
        # Arrange
        input = ''
        expected = ''

        # Act
        actual = double_escape_double_quotes(input)

        # Assert
        self.assertEqual(expected, actual)

    def test_double_escape_double_quotes_input_is_None(self):
        # Arrange
        input = None
        expected = None

        # Act
        actual = double_escape_double_quotes(input)

        # Assert
        self.assertEqual(expected, actual)

    def test_double_escape_double_quotes_and_backslashes_happy_path(self):
        # Arrange
        input = '"key": "aws_amis", "value": "{\"us-east-1\":\"ami-5f709f34\",\"us-west-2\":\"ami-7f675e4f\"}"'
        expected = '\\"key\\": \\"aws_amis\\", \\"value\\": \\"{\\\"us-east-1\\\":\\\"ami-5f709f34\\\",\\\"us-west-2\\\":\\\"ami-7f675e4f\\\"}\\"'

        # Act
        actual = double_escape_double_quotes_and_backslashes(input)

        # Assert
        self.assertEqual(expected, actual)

    def test_double_escape_double_quotes_and_backslashes_input_is_empty(self):
        # Arrange
        input = ''
        expected = ''

        # Act
        actual = double_escape_double_quotes_and_backslashes(input)

        # Assert
        self.assertEqual(expected, actual)

    def test_double_escape_double_quotes_and_backslashes_input_is_None(self):
        # Arrange
        input = None
        expected = None

        # Act
        actual = double_escape_double_quotes_and_backslashes(input)

        # Assert
        self.assertEqual(expected, actual)

    def test_triple_escape_double_single_quotes_happy_path(self):
        # Arrange
        input = "Testing user's parameter"
        expected = "Testing user'\\''s parameter"

        # Act
        actual = triple_escape_double_single_quotes(input)

        # Assert
        self.assertEqual(expected, actual)


    def test_triple_escape_double_single_quotes_input_is_None(self):
        # Arrange
        input = None
        expected = None

        # Act
        actual = triple_escape_double_single_quotes(input)

        # Assert
        self.assertEqual(expected, actual)


    def test_triple_escape_double_single_quotes_input_is_empty(self):
        # Arrange
        input = ''
        expected = ''

        # Act
        actual = triple_escape_double_single_quotes(input)

        # Assert
        self.assertEqual(expected, actual)
    
    def test_escape_quotes_backslashes_happy_path(self):
        # Arrange
        input = [None, '', '"key": "aws_amis", "value": "{\"us-east-1\":\"ami-5f709f34\",\"us-west-2\":\"ami-7f675e4f\"}"', "Testing it's all good ?"]
        expected = [None, '', '\\"key\\": \\"aws_amis\\", \\"value\\": \\"{\\\"us-east-1\\\":\\\"ami-5f709f34\\\",\\\"us-west-2\\\":\\\"ami-7f675e4f\\\"}\\"', "Testing it'\\''s all good ?"]
        
        for index, data in enumerate(input):
            # Act
            actual = escape_quotes_backslashes(data)

            # Assert
            self.assertEqual(expected[index], actual)

if __name__ == '__main__':
    main()
