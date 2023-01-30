DEFAULT_USER = 'ec2-user'

def create_runuser_command_with_default_user(base_command: str) -> str:
    """Creates a CLI runuser command using a base command and a default user"""
    if not base_command:
        raise ValueError('base_command must be a non-empty string')
    return f"runuser -l {DEFAULT_USER} -c '{base_command}'"

def double_escape_double_quotes(input: str) -> str:
    """Adds double-escape backslashes to any double quotes in a string. 
    Used to prepare a string to be embedded in quoted commands.
    If input is empty or None, input is returned.
    """
    if not input:
        return input
    return input.replace('"', '\\"')

def double_escape_double_quotes_and_backslashes(input: str) -> str:
    """Adds double-escape backslashes to any double quote and existing backslash in a string.
    Used to prepare a parameter string to be embedded in quoted commands.
    If input is empty or None, input is returned.
    """
    if not input:
        return input
    if '\\' in input:
        input = input.replace('\\', '\\\\')
    return input.replace('"', '\\"')
