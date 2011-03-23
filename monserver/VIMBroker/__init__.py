
from monserver.utils.load_config import load_global_config

config = load_global_config()

vim_name = config.get('VIM', 'crane')
vim = getattr(__import__('.'.join(['monserver', 'VIMBroker']), 
                 globals(), locals(), 
                 [vim_name,]), vim_name)


__all__ = ['vim']
