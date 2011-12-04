import os

from monagent.utils.load_config import load_global_config

config = load_global_config()
os.environ['xm_path'] = config.get('xm_path')
os.environ['xentop_path'] = config.get('xentop_path')
