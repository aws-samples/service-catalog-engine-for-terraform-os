import json
from json.decoder import JSONDecodeError

BACKEND_FILE_NAME = "backend_override.tf.json"
VARIABLE_FILE_NAME = "variable_override.tf.json"
PROVIDER_FILE_NAME = "provider_override.tf.json"
MAX_SESSION_NAME_LENGTH = 64


def write_backend_override(workspace_dir, provisioned_product_descriptor, state_bucket, state_region):
    backend_override = {
        "terraform": {
            "backend": {
                "s3": {
                    "bucket": f"{state_bucket}",
                    "key": f"{provisioned_product_descriptor}",
                    "region": f"{state_region}"
                }
            }
        }
    }
    with open(f"{workspace_dir}/{BACKEND_FILE_NAME}", "w") as json_file:
        json.dump(backend_override, json_file)


def write_variable_override(workspace_dir, variables):
    if not variables:
        return

    variable_override = {'variable': {}}
    for variable in variables:
        try:
            variable_value_json = json.loads(variable['value'])
            variable_override['variable'][variable['key']] = {"default": variable_value_json}
        except JSONDecodeError:
            variable_override['variable'][variable['key']] = {"default": variable['value']}
    with open(f"{workspace_dir}/{VARIABLE_FILE_NAME}", "w") as json_file:
        json.dump(variable_override, json_file)


def write_provider_override(workspace_dir, provisioned_product_descriptor, launch_role_arn, region, tags):
    provider_override = {
        "provider": {
            "aws": {
                "region": f"{region}",
                "assume_role": {
                    "role_arn": f"{launch_role_arn}",
                    "session_name": __format_session_name(provisioned_product_descriptor)
                },
                'default_tags': {
                    'tags': {
                    }
                }
            }
        }
    }

    if tags != None:
        for tag in tags:
            key = tag['key']
            provider_override['provider']['aws']['default_tags']['tags'][f'{key}'] = tag['value']

    with open(f"{workspace_dir}/{PROVIDER_FILE_NAME}", "w") as json_file:
        json.dump(provider_override, json_file)


def __format_session_name(unformatted_session_name):
    return f"{unformatted_session_name[:MAX_SESSION_NAME_LENGTH]}".replace('/', '-')
