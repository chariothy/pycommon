import unittest, os, logging
from chariothy_common import deep_merge, send_email, AppTool

MAIL = {
    'from': ('Hongyu TIAN', 'henrytian@163.com'),
    'to': (('Hongyu TIAN', 'henrytian@163.com'),)
}

SMTP = {
    'server': 'smtp.163.com',
    'port': 25,
    'user': 'henrytian@163.com',
    'pwd': '123456'
}

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app_tool = AppTool('test', os.getcwd())

    def test_app_tool(self):
        logger = self.app_tool.init_logger(SMTP, MAIL['from'], MAIL['to'])
        self.assertLogs(logger, logging.INFO)
        self.assertLogs(logger, logging.DEBUG)
        self.assertLogs(logger, logging.ERROR)

    def test_deep_merge(self):
        dict1 = {
            'a1': 1, 
            'a2': {
                'b1': 2,
                'b2': 3
            }
        }
        dict2 = {
            'a2': {
                'b2': 4,
                'b3': 5
            }
        }
        dict3 = {
            'a1': 1, 
            'a2': {
                'b1': 2,
                'b2': 4,
                'b3': 5
            }
        }
        self.assertDictEqual(deep_merge(dict1, dict2), dict3)

if __name__ == '__main__':
    unittest.main()