from unittest import main, TestCase

from notify.outputs import convert_state_file_outputs_to_service_catalog_outputs

class TestOutputs(TestCase):

    def test_convert_state_file_outputs_to_service_catalog_outputs_happy_path(self):
        # Arrange
        input = {"outputs":
            [
                {
                    "key": "key1",
                    "value": "value1",
                    "description": "desc1"
                },
                {
                    "key": "key2",
                    "value": "value2"
                },
                {
                    "key": "key3",
                    "value": "value3",
                    "description": None
                }
            ]
        }

        expected =[
            {
                "OutputKey": "key1",
                "OutputValue": "value1",
                "Description": "desc1"
            },
            {
                "OutputKey": "key2",
                "OutputValue": "value2"
            },
            {
                "OutputKey": "key3",
                "OutputValue": "value3"
                }
            ]

        # Act
        actual = convert_state_file_outputs_to_service_catalog_outputs(input)

        # Assert
        self.assertEqual(expected, actual)


    def test_convert_state_file_outputs_to_service_catalog_outputs_empty_list(self):
        # Act
        actual = convert_state_file_outputs_to_service_catalog_outputs({"outputs": []})

        # Assert
        self.assertEqual([], actual)

    def test_convert_state_file_outputs_to_service_catalog_outputs_outputs_missing(self):
        # Act
        actual = convert_state_file_outputs_to_service_catalog_outputs({})

        # Assert
        self.assertEqual([], actual)

if __name__ == '__main__':
    main()
