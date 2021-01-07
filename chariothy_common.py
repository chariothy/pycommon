import os, sys, logging
from os import path
from email.utils import formataddr
from collections.abc import Iterable
from logging import handlers
import functools
import platform
import warnings
import copy
from datetime import datetime
import time
import random
import json
import re

from exception import AppToolError

REG_NUM_INDEX = re.compile(r'\[([\+\-]?\d+)\]')

WIN = 'Windows'
LINUX = 'Linux'
DARWIN = 'Darwin'
os_sys = platform.system()

def is_win():
    return os_sys == WIN

def is_linux():
    return os_sys == LINUX

def is_darwin():
    return os_sys == DARWIN

def is_macos():
    return is_darwin()

def cls():
    if is_win():
        os.system('cls')
    elif is_linux() or is_macos():
        os.system('clear')

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)
    return new_func

def get_home_dir():
    from os.path import expanduser
    return expanduser('~')


def deep_merge_in(dict1: dict, dict2: dict) -> dict:
    """Deeply merge dictionary2 into dictionary1
    
    Arguments:
        dict1 {dict} -- Dictionary female
        dict2 {dict} -- Dictionary mail to be added to dict1
    
    Returns:
        dict -- Merged dictionary
    """
    if type(dict1) == dict and type(dict2) == dict:
        for key in dict2.keys():
            if key in dict1.keys() and type(dict1[key]) == dict and type(dict2[key]) == dict:
                deep_merge_in(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
    return dict1


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Deeply merge dictionary2 and dictionary1 then return a new dictionary
    
    Arguments:
        dict1 {dict} -- Dictionary female
        dict2 {dict} -- Dictionary mail to be added to dict1
    
    Returns:
        dict -- Merged dictionary
    """
    if type(dict1) == dict and type(dict2) == dict:
        dict1_copy = dict1.copy()
        for key in dict2.keys():
            if key in dict1.keys() and type(dict1[key]) == dict and type(dict2[key]) == dict:
                dict1_copy[key] = deep_merge(dict1[key], dict2[key])
            else:
                dict1_copy[key] = dict2[key]
        return dict1_copy
    return dict1


def send_email(from_addr, to_addrs, subject: str, body: str, smtp_config: dict, debug: bool=False) -> dict:
    """Helper for sending email
    
    Arguments:
        from_addr {str|tuple} -- From address, can be email or (name, email).
            Ex.: ('Henry TIAN', 'henrytian@163.com')
        to_addrs {str|tuple} -- To address, can be email or list of emails or list of (name, email)
            Ex.: (('Henry TIAN', 'henrytian@163.com'),)
        subject {str} -- Email subject
        body {str} -- Email body
        smtp_config {dict} -- SMTP config for SMTPHandler (default: {{}}), Ex.: 
        {
            'host': 'smtp.163.com',
            'port': 465,
            'user': 'henrytian@163.com',
            'pwd': '123456',
            'type': 'plain'         # plain (default) / ssl / tls
        }
        debug {bool} -- If output debug info.
        
    Returns:
        dict -- Email sending errors. {} if success, else {receiver: message}.
    """
    assert(type(from_addr) in (str, tuple, list))
    assert(type(to_addrs) in (str, tuple, list))
    assert(type(subject) == str)
    assert(type(body) == str)
    assert(type(smtp_config) == dict)

    #TODO: Use schema to validate smtp_config
    
    if type(from_addr) in (tuple, list):
        assert(len(from_addr) == 2)
        from_addr = formataddr(from_addr)

    if type(to_addrs) in (tuple, list):
        assert(len(to_addrs) > 0)
        if type(to_addrs[0]) in (tuple, list):
            #All (name, tuple)
            to_addrs = [formataddr(addr) for addr in to_addrs]
            to_addr_str = ','.join(to_addrs)
        elif type(to_addrs[0]) == str:
            #All emails
            to_addr_str = ','.join(to_addrs)
    elif type(to_addrs) == str:
        to_addr_str = to_addrs

    from email.mime.text import MIMEText
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = from_addr
    msg['To'] = to_addr_str
    from email.header import Header
    msg['Subject'] = Header(subject, 'utf-8').encode()
        
    from smtplib import SMTP, SMTP_SSL
    if smtp_config.get('type') == 'ssl':
        server = SMTP_SSL(smtp_config['host'], smtp_config['port'])
    elif smtp_config.get('type') == 'tls':
        server = SMTP(smtp_config['host'], smtp_config['port'])
        server.starttls()
    else:
        server = SMTP(smtp_config['host'], smtp_config['port'])
    
    server.ehlo()
    if debug:
        server.set_debuglevel(1)
    server.login(smtp_config['user'], smtp_config['pwd'])

    result = server.sendmail(from_addr, to_addrs, msg.as_string())
    server.quit()
    return result


def alignment(s, space, align='left'):
    """中英文混排对齐
    中英文混排时对齐是比较麻烦的，一个先决条件是必须是等宽字体，每个汉字占2个英文字符的位置。
    用print的格式输出是无法完成的。
    另一个途径就是用字符串的方法ljust, rjust, center先填充空格。但这些方法是以len()为基准的，即1个英文字符长度为1，1个汉字字符长度为3(uft-8编码），无法满足我们的要求。
    本方法的核心是利用字符的gb2312编码，正好长度汉字是2，英文是1。
    
    Arguments:
        s {str} -- 原字符串
        space {int} -- 填充长度
    
    Keyword Arguments:
        align {str} -- 对齐方式 (default: {'left'})
    
    Returns:
        str -- 对齐后的字符串

    Example:
        alignment('My 姓名', ' ', 'right')
    """
    length = len(s.encode('gb2312', errors='ignore'))
    space = space - length if space >= length else 0
    if align == 'left':
        s1 = s + ' ' * space
    elif align == 'right':
        s1 = ' ' * space + s
    elif align == 'center':
        s1 = ' ' * (space // 2) + s + ' ' * (space - space // 2)
    return s1


def get_win_dir(name):
    r"""Get windows folder path
       Read from \HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders
    
    Arguments:
        name {str} -- Name of folder path. 
        Ex. AppData, Favorites, Font, History, Local AppData, My Music, SendTo, Start Menu, Startup
            My Pictures, My Video, NetHood, PrintHood, Programs, Recent Personal, Desktop, Templates
        Note: Personal == My Documents
    """
    assert is_win()
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    try:
        return winreg.QueryValueEx(key, name)[0]
    except FileNotFoundError:
        return None

@deprecated
def get_win_folder(name):
    return get_win_folder(name)


def get(dictionary: dict, key:str, default=None, check:bool=False, replacement_for_dot_in_key:str=None):
    """Get value in dictionary, keys are connected by dot, and use environment value if exists
    Get dictionary value, 
        - if key exists in environment, use env value,
        - else then if exists in dictionary, use dictionary item value,
        - else then return default value.
    Ex. _dict = {
            'a': {
                'b': 'c', 
                'd': [
                    [{'e': 'f'}]
                ]
            }
        }
        1. get('a.b', 'e') == 'c'
        
        1. get('a.c', 'e') == 'e'
        
        1. getx('a.b[0][0].e') , getx('a.b[-1][0].e')
        - will return 'f'.

    If you have to use item key with dot, you can use replacement_for_dot_in_key.
    Ex. _dict = {'a': {'b.c': 'd'}}
        3. getx('a.b#c', replacement_for_dot_in_key='#')
        - will retuurn 'd' (if no replacement_for_dot_in_key will return None)


    Args:
        dictionary (dict): dictionary data
        key (str): Key for config item which are coneected by dot.
        default (any, optional): Default value if key does exist. Defaults to None.
        replacement_for_dot_in_key (str, optional): To support keys like "a.b". If "#" is given, "a#b" can be recognized as "a.b" . Defaults to None.
        check (bool, optional): If True, func will raise exception if key does not exist . Defaults to False.

    Returns:
        any: return config value
    """
    key_parts = key.split('.')
    config = dictionary
    parsed_keys = []
    
    for key_part in key_parts:
        if replacement_for_dot_in_key:
            key_part = key_part.replace(replacement_for_dot_in_key, '.')
        parsed_keys.append(key_part)
        parsing_key = '.'.join(parsed_keys)
        config_str = f'Config("{parsing_key}")={config}'

        idx_parts = REG_NUM_INDEX.split(key_part)   # REG_NUM_INDEX.split('a[-1][0]') => ['a', '-1', '', '0', '']
        if len(idx_parts) == 1:
            # no numberic index
            # not array, it's a dict
            amend_parsed_key = '.'.join(parsed_keys[:-1])
            config_str = f'Config("{amend_parsed_key}")={config}'
            if check:
                if type(config) is not dict:
                    raise AppToolError(f'Failed to get config at "{parsing_key}": Config is not dict. {config_str}')

                if key_part not in config:
                    raise AppToolError(f'Failed to get config at "{parsing_key}": "{key_part}" is not in config. {config_str}')

            try:
                config = config.get(key_part, default)
            except (AttributeError, TypeError) as ex:
                if check:
                    raise AppToolError(f'Failed to get config at "{parsing_key}": {ex}. {config_str}')
                config = default
        else:
            # has numberic index
            # is list or tuple
            if idx_parts[0] == '':
                raise AppToolError(f'Failed to get config at "{parsing_key}": "{key_part}" should have parent.')
            if idx_parts[-1] != '':
                raise AppToolError(f'Failed to get config at "{parsing_key}": "{key_part}" should be at the tail.')

            key_indexes = list(filter(lambda x: x, idx_parts))
            key_indexes.reverse()
            key_part = key_indexes.pop()
            key_indexes.reverse()
            if type(config) is not dict or key_part not in config:
                raise AppToolError(f'Failed to get config at "{parsing_key}": "{key_part}" is not in config. {config_str}')

            config = config[key_part]
            amend_parsed_keys = parsed_keys[:-1]
            amend_parsed_keys.append(key_part)
            amend_parsed_key = '.'.join(amend_parsed_keys)
            config_str = f'Config("{amend_parsed_key}")={config}'
            if type(config) is not list and type(config) is not tuple:
                raise AppToolError(f'Failed to get config at "{parsing_key}": Config is not list or tuple. {config_str}')
                
            for key_index in key_indexes:
                try:
                    key_index = int(key_index)
                    config = config[key_index]
                except (ValueError, IndexError) as ex:
                    raise AppToolError(f'Failed to get config at "{parsing_key}": Invalid index "{key_index}", {ex}. {config_str}')
        continue

        match = REG_NUM_INDEX.search(key_part)

        if match:
            # For list or tuple
            matched_str = match.group()
            matched_index = match.groups()[0]
            matched_start = match.start()
            matched_end = match.end()
            if matched_start == 0:
                raise AppToolError(f'Failed to get config at "{parsing_key}": "{matched_str}" should have parent.')
            if matched_end != len(key_part):
                raise AppToolError(f'Failed to get config at "{parsing_key}": "{matched_str}" should be at the tail.')

            key_part = key_part.replace(matched_str, '')
            if type(config) is not dict or key_part not in config:
                raise AppToolError(f'Failed to get config at "{parsing_key}": "{key_part}" is not in config. {config_str}')

            config = config[key_part]
            amend_parsed_keys = parsed_keys[:-1]
            amend_parsed_keys.append(key_part)
            amend_parsed_key = '.'.join(amend_parsed_keys)
            config_str = f'Config("{amend_parsed_key}")={config}'
            if type(config) is not list and type(config) is not tuple:
                raise AppToolError(f'Failed to get config at "{parsing_key}": Config is not list or tuple. {config_str}')

            key_index = int(matched_index)
            try:
                config = config[key_index]
            except IndexError as ex:
                raise AppToolError(f'Failed to get config at "{parsing_key}": Key index "{key_index}" is beyond size. {config_str}')
        else:
            # for dict
            amend_parsed_key = '.'.join(parsed_keys[:-1])
            config_str = f'Config("{amend_parsed_key}")={config}'
            if check:
                if type(config) is not dict:
                    raise AppToolError(f'Failed to get config at "{parsing_key}": Config is not dict. {config_str}')

                if key_part not in config:
                    raise AppToolError(f'Failed to get config at "{parsing_key}": "{key_part}" is not in config. {config_str}')

            try:
                config = config.get(key_part, default)
            except (AttributeError, TypeError) as ex:
                if check:
                    raise AppToolError(f'Failed to get config at "{parsing_key}": {ex}. {config_str}')
                config = default

    return config


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
        self._reg_index = re.compile(r'\[([\+\-]?\d+)\]')

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


    def log(self, reRaise=False, message=''):
        """Decorator
        !!! Should be decorated first to avoid being shielded by other decorators, such as @click.
        
        Keyword Arguments:
            reRaise {bool} -- Re-raise exception (default: {False})
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
                    if reRaise:
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


class GetCh:
    """Gets a single character from standard input.  Does not echo to the screen.
       Ex. getch = GetCh()
           ch = getch()
    """
    def __init__(self):
        os_name = platform.system()
        if is_win():
            self.impl = _GetchWindows()
        elif is_linux():
            self.impl = _GetchUnix()
        elif is_macos():
            # Patch for MACOS for now
            self.impl = lambda : input()

    def __call__(self): return str(self.impl())


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return str(msvcrt.getch(), encoding='utf-8')


def benchmark(func):
    """This is a decorator which can be used to benchmark time elapsed during running func."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        end = datetime.now()
        elapsed = (end - start).microseconds
        print(f'Elapsed {elapsed} ms during running {func.__name__}')
        return result
    return new_func


def random_sleep(min=0, max=3):
    time.sleep(random.uniform(min, max))


def load_json(file_path, default=None):
    data = default
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf8') as fp:
            data = json.load(fp)
    return data


def dump_json(file_path, data, indent=2, ensure_ascii=False, lock=False):
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(file_path, 'w', encoding='utf8') as fp:
        if lock and is_win():
            import fcntl
            fcntl.flock(fp, fcntl.LOCK_EX)
        json.dump(data, fp, indent=indent, ensure_ascii=ensure_ascii)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def today():
    return time.strftime("%Y-%m-%d", time.localtime())