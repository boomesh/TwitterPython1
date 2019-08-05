"""
https://pypi.org/project/python-dotenv/
"""
from pathlib import Path  # python3 only
from dotenv import load_dotenv

ENV_PATH = Path('.') / '.env'
load_dotenv(dotenv_path=ENV_PATH)
