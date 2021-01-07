import os, sys, logging
from os import path
from email.utils import formataddr
from collections.abc import Iterable
from logging import handlers
import functools
import time

from .utils import deep_merge, send_email, get
from .exception import AppToolError


class MySMTPHandler(handlers.SMTPHandler):
    def getSubject(self, record):
        #all_formatter = logging.Formatter(fmt='%(name)s - %(levelno)s - %(levelname)s - %(pathname)s - %(filename)s - %(module)s - %(lineno)d - %(funcName)s - %(created)f - %(asctime)s - %(msecs)d  %(relativeCreated)d - %(thread)d -  %(threadName)s -  %(process)d - %(message)s ')        
        #print('Ex. >>> ',all_formatter.formatMessage(record))

        #help(record)
        #help(formatter)
        
        formatter = logging.Formatter(fmt=self.subject)
        return formatter.formatMessage(record)


class AppTool(object):
    def __init__(self, app_name: str, app_path: str, local_config_dir: str='', config_name: str='config'):
        self._app_name = app_name
        self._app_path = app_path
        self._config = {}
        self._logger = None

        self.load_config(local_config_dir, config_name)
        self.init_logger()


    @property
    def config(self):
        return self._config


    @property
    def logger(self):
        return self._logger


    def load_config(self, local_config_dir: str = '', config_name: str='config') -> dict:
        """Load config locally
        
        Keyword Arguments:
            local_config_dir {str} -- Dir name of local config files. (default: {''})
        
        Returns:
            [dict] -- Merged config dictionary.
        """
        assert(type(local_config_dir) == str)

        sys.path.append(self._app_path)
        try:
            self._config = __import__(config_name).CONFIG
        except Exception:
            self._config = {}

        config_local_path = path.join(self._app_path, local_config_dir)
        sys.path.append(config_local_path)
        try:
            config_local = __import__(config_name + '_local').CONFIG
            self._config = deep_merge(self._config, config_local)
        except Exception:
            pass
        
        if '--test' in sys.argv:
            try:
                config_test = __import__(config_name + '_test').CONFIG
                self._config = deep_merge(self._config, config_test)
            except Exception:
                pass
        
        return self._config


    def init_logger(self) -> logging.Logger:
        """Initialize logger
        
        Returns:
            [logger] -- Initialized logger.
        """

        smtp = self._config.get('smtp')
        mail = self._config.get('mail')
        logConfig = self._config.get('log', {})

        logs_path = path.join(self._app_path, 'logs')
        if not os.path.exists(logs_path):
            os.mkdir(logs_path)

        logger = logging.getLogger(self._app_name)
        logLevel = logConfig.get('level', logging.DEBUG)
        logger.setLevel(logLevel)

        logDest = logConfig.get('dest', [])

        if 'file' in logDest:
            rf_handler = handlers.TimedRotatingFileHandler(path.join(logs_path, f'{self._app_name}.log'), when='D', interval=1, backupCount=7)
            rf_handler.suffix = "%Y-%m-%d_%H-%M-%S.log"
            rf_handler.level = logging.INFO
            rf_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(rf_handler)

        if smtp and 'mail' in logDest:
            from_addr = mail.get('from', (smtp['user'], smtp['user']))
            #TODO: Use schema to validate smtp
            assert(type(from_addr) in (tuple, list) and len(from_addr) == 2)
            from_addr = formataddr(from_addr)

            to_addrs = logConfig.get('receiver', mail.get('to'))
            assert(len(to_addrs) > 0 and type(to_addrs[0]) in (tuple, list))
            #All (name, tuple)
            to_addrs = [formataddr(addr) for addr in to_addrs]

            mail_handler = MySMTPHandler(
                    mailhost = (smtp['host'], smtp['port']),
                    fromaddr = from_addr,
                    toaddrs = to_addrs,
                    subject = '%(name)s - %(levelname)s - %(message)s',
                    credentials = (smtp['user'], smtp['pwd']))
            mail_handler.setLevel(logging.ERROR)
            logger.addHandler(mail_handler)

        if 'stdout' in logDest:
            st_handler = logging.StreamHandler()
            st_handler.level = logging.DEBUG
            st_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(st_handler)
        self._logger = logger
        return logger


    def send_email(self, subject: str, body: str, to_addrs=None, debug: bool=False) -> dict:
        """A shortcut of global send_email
        """
        smtp = self._config.get('smtp')
        mail = self._config.get('mail')
        #TODO: Use schema to validate smtp_config
        assert(smtp and mail)
        mail_to = to_addrs if to_addrs else mail['to']
        return send_email(mail['from'], mail_to, subject, body, smtp, debug)


    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)


    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)


    def warn(self, msg, *args, **kwargs):
        self._logger.warn(msg, *args, **kwargs)


    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)


    def err(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)


    def ex(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)


    def fatal(self, msg, *args, **kwargs):
        self._logger.fatal(msg, *args, **kwargs)


    def log(self, throw=False, message=''):
        """Decorator
        !!! Should be decorated first to avoid being shielded by other decorators, such as @click.
        
        Keyword Arguments:
            throw {bool} -- Re-raise exception (default: {False})
            message {str} -- Specify message
        
        Raises:
            ex: Original exception
        
        Example:
            @log()
            def func():
                pass

            @log(True)
            def func():
                pass

            @log(message='foo')
            def func():
                pass
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                try:
                    return func(*args, **kw)
                except Exception as ex:
                    self._logger.exception(message if message else str(ex))
                    if throw:
                        raise ex
            return wrapper
        return decorator


    def get(self, key:str, default=None, check:bool=False, replacement_for_dot_in_key:str='#'):
        """Get config value, keys are connected by dot, and use environment value if exists
        Get config value, 
            - if key exists in environment, use env value,
            - if not, then if exists in config, use config item value,
            - if not, then return default value.
        Ex. _config = {
                'a': {
                    'b': 'c', 
                    'd': [
                        [{'e': 'f'}]
                    ]
                }
            }
            1. getx('a.b', 'e')
            - if defined environment varible A_B = 'd', then return 'd',
            - else see get(dictionary: dict, key:str, default=None, check:bool=False, replacement_for_dot_in_key:str=None)
            
            2. getx('a.b[0].e') , getx('a.b[-1].e')
            - if defined environment varible A_B_0_0_E = 'd', then return 'd',
            - else see get(dictionary: dict, key:str, default=None, check:bool=False, replacement_for_dot_in_key:str=None)

        If you have to use item key with dot, you can use replacement_for_dot_in_key.
        Ex. _config = {'a': {'b.c': 'd'}}
            3. getx('a.b#c', replacement_for_dot_in_key='#')
            - if defined environment varible A_B_C = 'd', then return 'd',
            - else see get(dictionary: dict, key:str, default=None, check:bool=False, replacement_for_dot_in_key:str=None)


        Args:
            key (str): Key for config item which are coneected by dot.
            default (any, optional): Default value if key does exist. Defaults to None.
            replacement_for_dot_in_key (str, optional): To support keys like "a.b". If "#" is given, "a#b" can be recognized as "a.b" . Defaults to None.
            check (bool, optional): If True, func will raise exception if key does not exist . Defaults to False.

        Returns:
            any: return config value
        """
        full_key = self._app_name + '_' + key.replace('.', '_').replace('[', '_').replace(']', '').replace(' ', '_')
        if replacement_for_dot_in_key:
            full_key = full_key.replace(replacement_for_dot_in_key, '_')
        full_key = full_key.upper()
        if full_key in os.environ.keys():
            return os.environ.get(full_key)

        return get(self._config, key, default, check, replacement_for_dot_in_key)


    def __getitem__(self, key):
        return self.get(key, replacement_for_dot_in_key='#', check=True)