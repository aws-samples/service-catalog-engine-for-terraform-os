import logging

from core.configuration import Configuration
from core.exception import log_exception
from core.service_catalog_facade import ServiceCatalogFacade
from notify.errors import workflow_has_error, get_failure_reason
from notify.outputs import convert_state_file_outputs_to_service_catalog_outputs

# Globals
log = logging.getLogger()
log.setLevel(logging.INFO)
app_config = None
service_catalog_facade = None

# Input keys
WORKFLOW_TOKEN_KEY = 'token'
RECORD_ID_KEY = 'recordId'
TRACER_TAG_KEY = 'tracerTag'
TRACER_TAG_KEY_KEY = 'key'
TRACER_TAG_VALUE_KEY = 'value'


def __notify_succeeded(event):
    service_catalog_facade.notify_provision_succeeded(
                workflow_token = event[WORKFLOW_TOKEN_KEY],
                record_id = event[RECORD_ID_KEY],
                tracer_tag_key = event[TRACER_TAG_KEY][TRACER_TAG_KEY_KEY],
                tracer_tag_value = event[TRACER_TAG_KEY][TRACER_TAG_VALUE_KEY],
                outputs = convert_state_file_outputs_to_service_catalog_outputs(event)
            )

def __notify_failed(event):
            service_catalog_facade.notify_provision_failed(
                workflow_token = event[WORKFLOW_TOKEN_KEY],
                record_id = event[RECORD_ID_KEY],
                failure_reason = get_failure_reason(event),
                tracer_tag_key = event[TRACER_TAG_KEY][TRACER_TAG_KEY_KEY],
                tracer_tag_value = event[TRACER_TAG_KEY][TRACER_TAG_VALUE_KEY],
                outputs = convert_state_file_outputs_to_service_catalog_outputs(event)
            )

def notify(event, context):
    log.info(f'Handling event {event}')

    global app_config
    global service_catalog_facade

    try:
        if not app_config:
            app_config = Configuration()
        if not service_catalog_facade:
            service_catalog_facade = ServiceCatalogFacade(app_config)

        if workflow_has_error(event):
            __notify_failed(event)
        else:
            __notify_succeeded(event)

    except Exception as exception:
        log_exception(exception)
        raise exception
