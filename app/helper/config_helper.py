import configparser
from app import config


class Config_Helper:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str

    def get_section(self, section_name=''):
        if len(section_name) == 0:
            return ''
        else:
            returnVal = list(self.config.items(section_name))
            return returnVal

    def get_value(self, section_name='', variable_name=''):
        if len(section_name) == 0 or len(variable_name) == 0:
            return ''
        else:
            return self.config[section_name][variable_name]

    def set_value(self, section_name, variable_name='', variable_value=''):
        if len(variable_name) == 0 and len(variable_value) == 0:
            self.config.add_section(section_name)
        else:
            self.config.set(section_name, variable_name, variable_value)
            with open(config.CONFIG_PATH + '\Config.ini', 'w+', encoding="utf16") as f:
                self.config.write(f, space_around_delimiters=False)

    def remove_variable(self, section_name, variable_name=''):
        if len(variable_name) == 0:
            self.config.remove_section(section_name)
        else:
            self.config.remove_option(section_name, variable_name)

    def initSection(self, section_name):
        self.config.remove_section(section_name)
        self.config.add_section(section_name)
