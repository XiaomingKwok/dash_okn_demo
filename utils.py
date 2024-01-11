import configparser
from sumolib import checkBinary
import os
import sys

def import_config(config_file='config.ini'):
    content = configparser.ConfigParser()
    content.read(config_file)
    config = {}
    config['openai_key'] = content['openai']['key']
    config['neo4j_url'] = content['neo4j']['url']
    config['neo4j_user'] = content['neo4j']['user']
    config['neo4j_password'] = content['neo4j']['password']
    return config