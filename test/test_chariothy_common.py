import unittest, os, logging

from chariothy_common import deep_merge, deep_merge_in, benchmark, is_win, is_linux, is_macos, is_darwin
from chariothy_common import random_sleep, dump_json, load_json, send_email, get
from chariothy_common import AppTool, AppToolError

from config_test import CONFIG


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


class CoreTestCase(unittest.TestCase):
    def setUp(self):
        from os import environ as env
        self.demo_value = 'DEMO_VALUE'
        env['TEST_DEMO_KEY'] = self.demo_value # The first TEST is app_name
        env['TEST_DEMO_HOST'] = self.demo_value
        env['TEST_DEMO_KEY_FROM_0'] = self.demo_value
        env['TEST_DEMO_KEY_FROM_0_0'] = self.demo_value
        
        self.APP_NAME = 'test'
        self.APP = AppTool(self.APP_NAME, os.getcwd(), config_name='config_test')
        #print(self.APP.config)

    def test_app_tool(self):
        logger = self.APP.init_logger()
        self.assertLogs(logger, logging.INFO)
        self.assertLogs(logger, logging.DEBUG)
        self.assertLogs(logger, logging.ERROR)

    def test_deep_merge_in(self):
        self.assertDictEqual(deep_merge_in(dict1, dict2), dict3)
        self.assertDictEqual(dict1, dict3)

    def test_deep_merge(self):
        self.assertDictEqual(deep_merge(dict1, dict2), dict3)
        self.assertDictEqual(dict1, dict_ori)

    def test_is_win(self):
        self.assertTrue(is_win())

    def test_is_linux(self):
        self.assertFalse(is_linux())
    
    def test_is_macos(self):
        self.assertFalse(is_macos())

    def test_is_darwin(self):
        self.assertFalse(is_darwin())

    @benchmark
    def test_benchmark(self):
        import time
        time.sleep(1)

    def test_random_sleep(self):
        random_sleep()

    def test_load_json(self):
        self.assertIsNone(load_json('/not-exist-file-path'))

    def test_dump_json(self):
        file_path = './data/dump.json'
        data = {'test': 'OK'}
        dump_json(file_path, data)
        self.assertTrue(os.path.exists(file_path))
        
        load_data = load_json(file_path)
        self.assertDictEqual(data, load_data)

        os.remove(file_path)
    
    def test_get_config(self):
        """
        docstring
        """
        self.assertDictEqual(CONFIG, self.APP.config)

        self.assertTupleEqual(CONFIG['mail']['from'], self.APP.get('mail.from'))
        self.assertTupleEqual(CONFIG['mail']['from'], self.APP['mail.from'])

        self.assertEqual(CONFIG['mail']['from'][0], self.APP.get('mail.from[0]'))
        self.assertEqual(CONFIG['mail']['from'][-1], self.APP['mail.from[-1]'])

        self.assertEqual(CONFIG['mail']['to'][0][0], self.APP.get('mail.to[0][0]'))

        self.assertRaises(AppToolError, lambda k: self.APP[k], 'mail.from.test')
        self.assertIsNone(self.APP.get('mail.from.test'))
        self.assertEqual(1, self.APP.get('mail.from.test', 1))

        self.assertRaises(AppToolError, lambda k: self.APP[k], 'mail.[0]')
        self.assertRaises(AppToolError, lambda k: self.APP.get(k), 'mail.[0]')

        self.assertRaises(AppToolError, lambda k: self.APP[k], 'mail.from[0]x')
        self.assertRaises(AppToolError, lambda k: self.APP.get(k), 'mail.from[0]x')

        self.assertRaises(AppToolError, lambda k: self.APP[k], 'mail.fromx[0]')
        self.assertRaises(AppToolError, lambda k: self.APP.get(k), 'mail.fromx[0]')

        self.assertRaises(AppToolError, lambda k: self.APP[k], 'mail.smtp[0]')
        self.assertRaises(AppToolError, lambda k: self.APP.get(k), 'mail.smtp[0]')

        self.assertRaises(AppToolError, lambda k: self.APP[k], 'mail.smtp.port.test')
        self.assertIsNone(self.APP.get('mail.smtp.port.test'))
        self.assertEqual(1, self.APP.get('mail.smtp.port.test', 1))
        
        self.assertEqual(CONFIG['demo.key2']['from'][0], self.APP['demo#key2.from[0]'])
        self.assertRaises(AppToolError, lambda k: self.APP[k], 'demo#key.from[0]') # Because now demo.key is replaced by env

        self.assertEqual(self.demo_value, self.APP['demo#key'])
        self.assertEqual(self.demo_value, self.APP['demo.host'])


    def test_send_text_email(self):
        """
        docstring
        """
        result = send_email(
            self.APP['mail.from'], 
            self.APP['mail.to'], 
            'Send text mail for chariothy_common',
            'Send text mail for chariothy_common',
            self.APP['smtp'],
            send_to_file=self.APP['mail.dest']!='mail'
        )
        self.assertDictEqual(result, {})

    def test_send_html_email(self):
        """
        docstring
        """
        body = """
<h3>Hi，all</h3>
<p>附件为本次自动化测试报告。</p>
"""
        result = send_email(
            self.APP['mail.from'], 
            self.APP['mail.to'], 
            'Send html mail for chariothy_common',
            smtp_config=self.APP['smtp'],
            html_body=body,
            send_to_file=self.APP['mail.dest']!='mail'
        )
        self.assertDictEqual(result, {})


    def test_send_html_email_with_img(self):
        """
        docstring
        """
        body = """
<h3>Hi，all</h3>
<p>附件为本次自动化测试报告。</p>
<p><img src="cid:{}"></p>
<p><img src="cid:{}"></p>
"""
        pwd = os.path.dirname(__file__)
        images = (
            os.path.join(pwd, 'train.png'),
            os.path.join(pwd, 'boat.png'),
        )
        result = send_email(
            self.APP['mail.from'], 
            self.APP['mail.to'], 
            'Send html mail with image for chariothy_common',
            smtp_config=self.APP['smtp'],
            html_body=body,
            image_paths=images,
            send_to_file=self.APP['mail.dest']!='mail'
        )
        self.assertDictEqual(result, {})


    def test_send_html_email_with_file(self):
        """
        docstring
        """
        body = """
<h3>Hi，all</h3>
<p>附件为本次自动化测试报告。</p>
"""
        pwd = os.path.dirname(__file__)
        files = (
            os.path.join(pwd, 'train.png'),
            os.path.join(pwd, 'boat.png'),
        )
        result = send_email(
            self.APP['mail.from'], 
            self.APP['mail.to'], 
            'Send html mail with file for chariothy_common',
            smtp_config=self.APP['smtp'],
            html_body=body,
            file_paths=files,
            send_to_file=self.APP['mail.dest']!='mail'
        )
        self.assertDictEqual(result, {})


if __name__ == '__main__':
    unittest.main()