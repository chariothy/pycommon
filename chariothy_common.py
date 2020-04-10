import os, sys, logging
from os import path
from email.utils import formataddr
from collections.abc import Iterable
from logging import handlers
import functools


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Deeply merge two dictionaries
    
    Arguments:
        dict1 {dict} -- Dictionary to be added
        dict2 {dict} -- Dictionary to be added to dict1
    
    Returns:
        dict -- Merged dictionary
    """
    if type(dict1) == dict and type(dict2) == dict:
        for key in dict2.keys():
            if key in dict1.keys() and type(dict1[key]) == dict and type(dict2[key]) == dict:
                deep_merge(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
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
            'port': 25,
            'user': 'henrytian@163.com',
            'pwd': '123456'
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
    smtp = smtp_config

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
        
    from smtplib import SMTP
    server = SMTP(smtp['host'], smtp['port'])
    if debug:
        server.set_debuglevel(1)
    server.login(smtp['user'], smtp['pwd'])

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


def get_win_folder(name):
    """Get windows folder path
       Read from \HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders
    
    Arguments:
        name {str} -- Name of folder path. 
        Ex. AppData, Favorites, Font, History, Local AppData, My Music, SendTo, Start Menu, Startup
            My Pictures, My Video, NetHood, PrintHood, Programs, Recent Personal, Desktop, Templates
    """
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    try:
        return winreg.QueryValueEx(key, name)[0]
    except FileNotFoundError:
        return None


class MySMTPHandler(handlers.SMTPHandler):
    def getSubject(self, record):
        #all_formatter = logging.Formatter(fmt='%(name)s - %(levelno)s - %(levelname)s - %(pathname)s - %(filename)s - %(module)s - %(lineno)d - %(funcName)s - %(created)f - %(asctime)s - %(msecs)d  %(relativeCreated)d - %(thread)d -  %(threadName)s -  %(process)d - %(message)s ')        
        #print('Ex. >>> ',all_formatter.formatMessage(record))

        #help(record)
        #help(formatter)
        
        formatter = logging.Formatter(fmt=self.subject)
        return formatter.formatMessage(record)

class AppTool(object):
    def __init__(self, app_name: str, app_path: str, config_dir: str='', log_mail_to=''):
        self.app_name = app_name
        self.app_path = app_path
        self.config = {}
        self.logger = None

        self.load_config(config_dir)

        smtp = self.config['smtp']
        mail = self.config['mail']
        #TODO: Use schema to validate smtp_config
        if smtp and mail:
            if log_mail_to:
                self.init_logger(smtp, mail['from'], log_mail_to)
            else:
                self.init_logger(smtp, mail['from'], mail['to'])


    def load_config(self, config_dir: str = '') -> dict:
        """Load config locally
        
        Keyword Arguments:
            config_dir {str} -- Dir name of config files. (default: {''})
        
        Returns:
            [dict] -- Merged config dictionary.
        """
        assert(type(config_dir) == str)

        if self.config:
            return self.config

        configs_path = path.join(self.app_path, config_dir)
        sys.path.append(configs_path)
        if path.exists(path.join(configs_path, 'config.py')):
            config = __import__('config').CONFIG
        else:
            config = {}

        if path.exists(path.join(configs_path, 'config_local.py')):
            config_local = __import__('config_local').CONFIG
        else:
            config_local = {}
        self.config = deep_merge(config, config_local)
        
        if '--test' in sys.argv and path.exists(path.join(configs_path, 'config_test.py')):
            config_test = __import__('config_test').CONFIG
        else:
            config_test = {}
        self.config = deep_merge(config, config_test)
        
        return self.config


    def init_logger(self, smtp_config: dict={}, from_addr='', to_addrs='') -> logging.Logger:
        """Initialize logger
        
        Keyword Arguments:
            smtp_config {dict} -- SMTP config for SMTPHandler (default: {{}}), Ex.: 
                {
                    'host': 'smtp.163.com',
                    'port': 25,
                    'user': 'henrytian@163.com',
                    'pwd': '123456'
                }
                If is an empty dict, try to read from config.
            from_addr {str|tuple} -- From address, can be email or (name, email).
                Ex.: ('Henry TIAN', 'henrytian@163.com')
                If is an empty str, try to read from config.
            to_addrs {str|tuple} -- To address, can be email or list of emails or list of (name, email)
                Ex.: (('Henry TIAN', 'henrytian@163.com'),)
                If is an empty str, try to read from config.
        Returns:
            [logger] -- Initialized logger.
        """
        assert(type(smtp_config) == dict)
        assert(type(from_addr) in (str, tuple, list))
        assert(type(to_addrs) in (str, tuple, list))

        if self.logger and not smtp_config:
            return self.logger

        logs_path = path.join(self.app_path, 'logs')
        if not os.path.exists(logs_path):
            os.mkdir(logs_path)

        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.DEBUG)

        rf_handler = handlers.TimedRotatingFileHandler(path.join(logs_path, f'{self.app_name}.log'), when='D', interval=1, backupCount=7)
        rf_handler.suffix = "%Y-%m-%d_%H-%M-%S.log"
        rf_handler.level = logging.INFO
        rf_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(rf_handler)

        if smtp_config:
            #TODO: Use schema to validate smtp_config
            smtp = smtp_config
            if type(from_addr) in (tuple, list):
                assert(len(from_addr) == 2)
                from_addr = formataddr(from_addr)

            if type(to_addrs) in (tuple, list):
                assert(len(to_addrs) > 0)
                if type(to_addrs[0]) in (tuple, list):
                    #All (name, tuple)
                    to_addrs = [formataddr(addr) for addr in to_addrs]

            mail_handler = MySMTPHandler(
                    mailhost = (smtp['host'], smtp['port']),
                    fromaddr = from_addr,
                    toaddrs = to_addrs,
                    subject = '[%(levelname)s] - %(name)s - %(message)s',
                    credentials = (smtp['user'], smtp['pwd']))
            mail_handler.setLevel(logging.ERROR)
            logger.addHandler(mail_handler)

        if os.environ.get('RUN_IN_CRON') != '1':
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