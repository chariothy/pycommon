import os, sys, logging
from os import path
from email.utils import formataddr
from collections.abc import Iterable


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


class TitledSMTPHandler(logging.handlers.SMTPHandler):
    def getSubject(self, record):
        formatter = logging.Formatter(fmt=self.subject)
        return formatter.format(record)

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

        if self.logger:
            return self.logger

        logs_path = path.join(self.app_path, 'logs')
        if not os.path.exists(logs_path):
            os.mkdir(logs_path)

        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.DEBUG)

        from logging import handlers

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

            mail_handler = TitledSMTPHandler(
                    mailhost = (smtp['host'], smtp['port']),
                    fromaddr = from_addr,
                    toaddrs = to_addrs,
                    subject = '%(name)s - %(levelname)s - %(message)s',
                    credentials = (smtp['user'], smtp['pwd']))
            mail_handler.setLevel(logging.ERROR)
            logger.addHandler(mail_handler)

        if not ('-b' in sys.argv or '--background' in sys.argv):
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