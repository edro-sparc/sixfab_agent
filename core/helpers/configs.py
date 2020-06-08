from configparser import ConfigParser

environments_object = ConfigParser()
environments_object.read("/opt/sixfab/.env")

def config_object_to_string(config_object):
    cache_string = ""
    
    def _section_parser(section_name):
        nonlocal cache_string
        nonlocal config_object

        cache_string += f"[{section_name}]\n"

        for key, value in config_object[section_name].items():
            cache_string += f"{key.upper()}={value}\n"

        cache_string += "\n"

    for section in config_object.sections():
        _section_parser(section)

    return cache_string
