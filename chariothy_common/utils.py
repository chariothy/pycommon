import os, sys
from os import path
from email.utils import formataddr
import functools
import platform
import warnings
import copy
from datetime import datetime
import time
import random
import json
import re
from typing import Union

from .exception import AppToolError

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
    if type(dict1) is dict and type(dict2) is dict:
        for key in dict2.keys():
            if key in dict1.keys() and type(dict1[key]) is dict and type(dict2[key]) is dict:
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
    if type(dict1) is dict and type(dict2) is dict:
        dict1_copy = dict1.copy()
        for key in dict2.keys():
            if key in dict1.keys() and type(dict1[key]) is dict and type(dict2[key]) is dict:
                dict1_copy[key] = deep_merge(dict1[key], dict2[key])
            else:
                dict1_copy[key] = dict2[key]
        return dict1_copy
    return dict1


def send_email(from_addr, to_addrs, subject: str, text_body: str='', smtp_config: dict={}, 
    html_body: str=None, 
    image_paths: Union[dict, tuple]=None, file_paths: Union[dict, tuple]=None, 
    debug: bool=False, send_to_file: bool=False, email_file_dir=None
    ) -> dict:
    """Helper for sending email
    
    Arguments:
        from_addr {str|tuple} -- From address, can be email or (name, email).
            Ex.: ('Henry TIAN', 'henrytian@163.com')
        to_addrs {str|tuple} -- To address, can be email or list of emails or list of (name, email)
            Ex.: (('Henry TIAN', 'henrytian@163.com'),)
        subject {str} -- Email subject
        text_body {str} -- Email text body
        html_body {str} -- Email html body
        image_paths {list|tuple} -- image file path array
        file_paths {list|tuple} -- attachment file path array
        smtp_config {dict} -- SMTP config for SMTPHandler (default: {{}}), Ex.: 
        {
            'host': 'smtp.163.com',
            'port': 465,
            'user': 'henrytian@163.com',
            'pwd': '123456',
            'type': 'plain'         # plain (default) / ssl / tls
        }
        debug {bool} -- If True output debug info.
        send_to_file {str} -- File path for writing email info to text file.
        
    Returns:
        dict -- Email sending errors. {} if success, else {receiver: message}.
    """
    assert(type(from_addr) in (str, tuple, list))
    assert(type(to_addrs) in (str, tuple, list))
    assert(type(subject) is str)
    assert(type(text_body) is str or type(html_body) is str)
    assert(type(smtp_config) is dict)

    if send_to_file:
        if not email_file_dir:
            email_file_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(email_file_dir):
            os.mkdir(email_file_dir)

    #TODO: Use schema to validate smtp_config
    
    if type(from_addr) in (tuple, list):
        assert(len(from_addr) == 2)
        from_addr = formataddr(from_addr)

    if type(to_addrs) in (tuple, list):
        assert(len(to_addrs) > 0)
        if type(to_addrs[0]) in (tuple, list):
            #All (name, tuple)
            to_addrs = (formataddr(addr) for addr in to_addrs)
            to_addr_str = ','.join(to_addrs)
        elif type(to_addrs[0]) is str:
            #All emails
            to_addr_str = ','.join(to_addrs)
    elif type(to_addrs) is str:
        to_addr_str = to_addrs

    from email.message import EmailMessage
    from email.utils import make_msgid
    from mimetypes import guess_type

    msg = EmailMessage()
    # generic email headers
    msg['From'] = from_addr
    msg['To'] = to_addr_str
    msg['Subject'] = subject

    # set the plain text body
    msg.set_content(text_body)

    if html_body:
        img_nodes = []
        if image_paths and len(image_paths) > 0:
            for image_path in image_paths:
                # print(guess_type(image_path)[0].split('/', 1))
                with open(image_path, 'rb') as fp:
                    img_nodes.append({
                        'cid': make_msgid('chariothy_common'),
                        'bin': fp.read(),
                        'type': guess_type(image_path)[0].split('/', 1)
                    })
            # note that we needed to peel the <> off the msgid for use in the html.
            html_body = html_body.format(*(x['cid'][1:-1] for x in img_nodes))
        msg.add_alternative(html_body, subtype='html')

        for img_node in img_nodes:
            maintype, subtype = img_node['type']
            msg.get_payload()[1].add_related(
                img_node['bin'],
                maintype=maintype, 
                subtype=subtype, 
                cid=img_node['cid']
            )

    if file_paths and len(file_paths) > 0:
        for file_path in file_paths:
            ctype, encoding = guess_type(file_path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            
            with open(file_path, 'rb') as fp:
                file_name = os.path.basename(file_path)
                msg.add_attachment(fp.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=file_name
                )
    
    if send_to_file or debug:
        email_file_name = now().replace(' ', '_').replace(':', '-') + '_' + str(random.randint(1000, 9999)) + '.txt'
        from email.policy import SMTP
        with open(os.path.join(email_file_dir, email_file_name), 'wb') as fp:
            fp.write(msg.as_bytes(policy=SMTP))
        result = {}

    if not send_to_file:
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

        #result = server.sendmail(from_addr, to_addrs, msg.as_string())
        result = server.send_message(msg)
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

    return config


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