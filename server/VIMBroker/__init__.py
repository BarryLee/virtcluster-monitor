
from server.utils.load_config import load_global_config

config = load_global_config()

vim = __import__(config.get('VIM', 'crane'))

__all__ == ["vim"]
