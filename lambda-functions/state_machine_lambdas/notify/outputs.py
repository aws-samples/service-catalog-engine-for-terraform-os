# Constants
OUTPUTS_KEY = 'outputs'
OUTPUT_KEY_KEY = 'key'
OUTPUT_VALUE_KEY = 'value'
OUTPUT_DESCRIPTION_KEY = 'description'

SC_OUTPUT_KEY_KEY = 'OutputKey'
SC_OUTPUT_VALUE_KEY = 'OutputValue'
SC_OUTPUT_DESCRIPTION_KEY = 'Description'

def convert_state_file_outputs_to_service_catalog_outputs(event: dict) -> list:
    """Converts the outputs in a lambda input event to the format for Service Catalog outputs"""
    if OUTPUTS_KEY not in event:
        return []

    service_catalog_outputs: list = []

    for state_file_output in event[OUTPUTS_KEY]:
        if OUTPUT_DESCRIPTION_KEY in state_file_output and state_file_output[OUTPUT_DESCRIPTION_KEY] is not None:
            service_catalog_outputs.append({
                SC_OUTPUT_KEY_KEY: state_file_output[OUTPUT_KEY_KEY],
                SC_OUTPUT_VALUE_KEY: state_file_output[OUTPUT_VALUE_KEY],
                SC_OUTPUT_DESCRIPTION_KEY: state_file_output[OUTPUT_DESCRIPTION_KEY]
            })
        else:
            service_catalog_outputs.append({
                SC_OUTPUT_KEY_KEY: state_file_output[OUTPUT_KEY_KEY],
                SC_OUTPUT_VALUE_KEY: state_file_output[OUTPUT_VALUE_KEY]
            })

    return service_catalog_outputs
