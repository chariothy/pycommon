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


def send_mail(from_addr, to_addrs, subject: str, body: str, smtp_config: dict, debug: bool=False) -> dict:
    """Alias to send_email
    """
    return send_email(from_addr, to_addrs, subject, body, smtp_config, debug)


def email(from_addr, to_addrs, subject: str, body: str, smtp_config: dict, debug: bool=False) -> dict:
    """Alias to send_email
    """
    return send_email(from_addr, to_addrs, subject, body, smtp_config, debug)


def mail(from_addr, to_addrs, subject: str, body: str, smtp_config: dict, debug: bool=False) -> dict:
    """Alias to send_email
    """
    return send_email(from_addr, to_addrs, subject, body, smtp_config, debug)


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


class MySMTPHandler(handlers.SMTPHandler):
    def getSubject(self, record):
        #all_formatter = logging.Formatter(fmt='%(name)s - %(levelno)s - %(levelname)s - %(pathname)s - %(filename)s - %(module)s - %(lineno)d - %(funcName)s - %(created)f - %(asctime)s - %(msecs)d  %(relativeCreated)d - %(thread)d -  %(threadName)s -  %(process)d - %(message)s ')        
        #print('Ex. >>> ',all_formatter.formatMessage(record))

        #help(record)
        #help(formatter)
        
        formatter = logging.Formatter(fmt=self.subject)
        return formatter.formatMessage(record)

class AppTool(object):
    def __init__(self, app_name: str, app_path: str, local_config_dir: str=''):
        self.app_name = app_name
        self.app_path = app_path
        self.config = {}
        self.logger = None

        self.load_config(local_config_dir)
        self.init_logger()


    def load_config(self, local_config_dir: str = '') -> dict:
        """Load config locally
        
        Keyword Arguments:
            local_config_dir {str} -- Dir name of local config files. (default: {''})
        
        Returns:
            [dict] -- Merged config dictionary.
        """
        assert(type(local_config_dir) == str)

        sys.path.append(self.app_path)
        try:
            config = __import__('config').CONFIG
        except Exception:
            pass

        config_local_path = path.join(self.app_path, local_config_dir)
        sys.path.append(config_local_path)
        try:
            config_local = __import__('config_local').CONFIG
            self.config = deep_merge(config, config_local)
        except Exception:
            pass        
        
        if '--test' in sys.argv:
            try:
                config_test = __import__('config_test').CONFIG
                self.config = deep_merge(self.config, config_test)
            except Exception:
                pass
        
        return self.config


    def init_logger(self) -> logging.Logger:
        """Initialize logger
        
        Returns:
            [logger] -- Initialized logger.
        """

        smtp = self.config.get('smtp')
        mail = self.config.get('mail')
        logConfig = self.config.get('log', {})

        logs_path = path.join(self.app_path, 'logs')
        if not os.path.exists(logs_path):
            os.mkdir(logs_path)

        logger = logging.getLogger(self.app_name)
        logLevel = logConfig.get('level', logging.DEBUG)
        logger.setLevel(logLevel)

        logDest = logConfig.get('dest', [])

        if 'file' in logDest:
            rf_handler = handlers.TimedRotatingFileHandler(path.join(logs_path, f'{self.app_name}.log'), when='D', interval=1, backupCount=7)
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
            st_handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(st_handler)
        self.logger = logger
        return logger


    def send_email(self, subject: str, body: str, to_addrs=None, debug: bool=False) -> dict:
        """A shortcut of global send_email
        """
        smtp = self.config['smtp']
        mail = self.config['mail']
        #TODO: Use schema to validate smtp_config
        assert(smtp and mail)
        mail_to = to_addrs if to_addrs else mail['to']
        return send_email(mail['from'], mail_to, subject, body, smtp, debug)


    def email(self, subject: str, body: str, to_addrs=None, debug: bool=False) -> dict:
        """Alias to send_email
        """
        return self.send_email(subject, body, to_addrs, debug)

    
    def mail(self, subject: str, body: str, to_addrs=None, debug: bool=False) -> dict:
        """Alias to send_email
        """
        return self.send_email(subject, body, to_addrs, debug)


    def send_mail(self, subject: str, body: str, to_addrs=None, debug: bool=False) -> dict:
        """Alias to send_email
        """
        return self.send_email(subject, body, to_addrs, debug)


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
                    self.logger.exception(message if message else str(ex))
                    if reRaise:
                        raise ex
            return wrapper
        return decorator


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


def load_json(file_path):
    data = None
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