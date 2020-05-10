import unittest, os, logging
import chariothy_common as cc

MAIL = {
    'from': ('Hongyu TIAN', 'henrytian@163.com'),
    'to': (('Hongyu TIAN', 'henrytian@163.com'),)
}

SMTP = {
    'host': 'smtp.163.com',
    'port': 25,
    'user': 'henrytian@163.com',
    'pwd': '123456'
}

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app_tool = cc.AppTool('test', os.getcwd())

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
        self.assertDictEqual(cc.deep_merge(dict1, dict2), dict3)

    def test_is_win(self):
        self.assertTrue(cc.is_win())

    def test_is_linux(self):
        self.assertFalse(cc.is_linux())

    def test_get_home_dir(self):
        self.assertEqual(cc.get_home_dir(), r'C:\Users\hytian3019')
    
    def test_is_macos(self):
        self.assertFalse(cc.is_macos())

    def test_is_darwin(self):
        self.assertFalse(cc.is_darwin())


    def test_get_win_folder(self):
        self.assertEqual(cc.get_win_dir('Desktop'), r'C:\Users\hytian3019\Desktop')

if __name__ == '__main__':
    unittest.main()