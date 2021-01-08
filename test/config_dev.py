CONFIG = {
    'log': {
        'level': 'ERROR',   # 与log库的level一致，包括DEBUG, INFO, ERROR
                            #   DEBUG   - Enable stdout, file, mail （如果在dest中启用）
                            #   INFO    - Enable file, mail         （如果在dest中启用）
                            #   ERROR   - Enable mail               （如果在dest中启用）
        'dest': ['file', 'mail'],  # 分别设置日志对象，优先级高于level设置
    },
    'mail': {
        'from': ['Henry TIAN', 'chariothy@gmail.com'],
        'to': [
            ['Henry TIAN', '6314888@qq.com'],
            ['Henry TIAN', 'chariothy@gmail.com']
        ]
    },
}