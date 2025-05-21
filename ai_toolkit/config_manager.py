#!/usr/bin/env python3

import configparser
from .setup import CONFIG_FILE, DEFAULT_SUMMARY_MODEL, DEFAULT_SUMMARY_MAX_TOKENS, \
    DEFAULT_DESCRIPTION_MODEL, DEFAULT_DESCRIPTION_MAX_TOKENS


def load_config():
    """Load configuration from CONFIG_FILE, returning dict of settings."""
    parser = configparser.ConfigParser()
    data = {}

    # Read existing config
    if CONFIG_FILE.exists():
        parser.read(CONFIG_FILE)

    # OpenAI section
    data['api_key'] = parser.get('OpenAI', 'api_key', fallback='')

    # AI section
    data['summary_model'] = parser.get('AI', 'summary_model', fallback=DEFAULT_SUMMARY_MODEL)
    data['summary_max_tokens'] = parser.getint('AI', 'summary_max_tokens', fallback=DEFAULT_SUMMARY_MAX_TOKENS)
    data['description_model'] = parser.get('AI', 'description_model', fallback=DEFAULT_DESCRIPTION_MODEL)
    data['description_max_tokens'] = parser.getint('AI', 'description_max_tokens', fallback=DEFAULT_DESCRIPTION_MAX_TOKENS)

    return data

