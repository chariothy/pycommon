import unittest, os, logging
import chariothy_common as cc
from config_sample import CONFIG
from exception import AppToolError


class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app_tool = cc.AppTool('test', os.getcwd(), config_name='config_sample')

    def test_app_tool(self):
        logger = self.app_tool.init_logger()
        self.assertLogs(logger, logging.INFO)
        self.assertLogs(logger, logging.DEBUG)
        self.assertLogs(logger, logging.ERROR)

    def test_deep_merge_in(self):
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
        self.assertDictEqual(cc.deep_merge_in(dict1, dict2), dict3)
        self.assertDictEqual(dict1, dict3)

    def test_deep_merge(self):
        dict1 = {
            'a1': 1, 
            'a2': {
                'b1': 2,
                'b2': 3
            }
        }
        dict_ori = {
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
        self.assertDictEqual(dict1, dict_ori)

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

    @cc.benchmark
    def test_benchmark(self):
        import time
        time.sleep(1)

    def test_random_sleep(self):
        cc.random_sleep()

    def test_load_json(self):
        self.assertIsNone(cc.load_json('/not-exist-file-path'))

    def test_dump_json(self):
        file_path = './data/dump.json'
        data = {'test': 'OK'}
        cc.dump_json(file_path, data)
        self.assertTrue(os.path.exists(file_path))
        
        load_data = cc.load_json(file_path)
        self.assertDictEqual(data, load_data)

        os.remove(file_path)
    
    
    def test_get_config(self):
        """
        docstring
        """
        self.assertDictEqual(CONFIG, self.app_tool.config)

        self.assertTupleEqual(CONFIG['mail']['from'], self.app_tool.get('mail.from'))
        self.assertTupleEqual(CONFIG['mail']['from'], self.app_tool['mail.from'])

        self.assertEqual(CONFIG['mail']['from'][0], self.app_tool.get('mail.from[0]'))
        self.assertEqual(CONFIG['mail']['from'][-1], self.app_tool['mail.from[-1]'])

        self.assertRaises(AppToolError, lambda k: self.app_tool[k], 'mail.from.test')
        self.assertIsNone(self.app_tool.get('mail.from.test'))
        self.assertEqual(1, self.app_tool.get('mail.from.test', 1))

        self.assertRaises(AppToolError, lambda k: self.app_tool[k], 'mail.[0]')
        self.assertRaises(AppToolError, lambda k: self.app_tool.get(k), 'mail.[0]')

        self.assertRaises(AppToolError, lambda k: self.app_tool[k], 'mail.from[0]x')
        self.assertRaises(AppToolError, lambda k: self.app_tool.get(k), 'mail.from[0]x')

        self.assertRaises(AppToolError, lambda k: self.app_tool[k], 'mail.fromx[0]')
        self.assertRaises(AppToolError, lambda k: self.app_tool.get(k), 'mail.fromx[0]')

        self.assertRaises(AppToolError, lambda k: self.app_tool[k], 'mail.smtp[0]')
        self.assertRaises(AppToolError, lambda k: self.app_tool.get(k), 'mail.smtp[0]')

        self.assertRaises(AppToolError, lambda k: self.app_tool[k], 'mail.smtp.port.test')
        self.assertIsNone(self.app_tool.get('mail.smtp.port.test'))
        self.assertEqual(1, self.app_tool.get('mail.smtp.port.test', 1))
        
        self.assertEqual(CONFIG['test.key']['from'][0], self.app_tool['test#key.from[0]'])

if __name__ == '__main__':
    unittest.main()