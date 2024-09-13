#-*- coding: UTF-8 -*-
import unittest
import sys
sys.path.insert(0, "../")
from ptutil import *

class test_ptutil(unittest.TestCase):
  def test_file_ops1(self):
    fp = './temp/1/2/3/4/5/6/7/8/test.txt'
    self.assertFalse(file_exists(fp))
    file_create(fp)
    file_write_all(fp, 'hello\r\nworld\tA\rB\nC')
    self.assertEqual(file_read(fp), 'hello\r\nworld\tA\rB\nC')
    self.assertTrue(file_exists(fp))
    file_delete(fp)
    self.assertFalse(file_exists(fp))
    path_delete('./temp')

  def test_file_ops2(self):
    fp = './test.txt'
    self.assertFalse(file_exists(fp))
    file_create(fp)
    file_write_all(fp, 'hello\r\nworld\tA\rB\nC')
    self.assertEqual(file_read(fp), 'hello\r\nworld\tA\rB\nC')
    self.assertTrue(file_exists(fp))
    file_delete(fp)
    self.assertFalse(file_exists(fp))

  def test_path_ops(self):
    fp = './temp/1/2/3/4/5/6/7/8'
    self.assertFalse(path_exists(fp))
    path_create(fp)
    self.assertTrue(path_exists(fp))
    path_delete('./temp')
    self.assertFalse(path_exists('./temp'))

  def test_path_files(self):
    fp = './temp'
    path_delete(fp)
    fs = ['./temp/a.txt',
          './temp/b.txt',
          './temp/c.txt',
          './temp/d.txt',
          './temp/1.py',
          './temp/2.py',
          './temp/3.py']

    self.assertFalse(path_exists(fp))
    path_create(fp)
    self.assertTrue(path_exists(fp))
    for f in fs:
      file_create(f)

    txt = path_files(fp,'*.txt')
    py = path_files(fp, '*.py')
    txt.sort()
    py.sort()

    self.assertEqual(len(txt), 4)
    self.assertEqual(len(py),  3)
    self.assertEqual(txt[0], './temp/a.txt')
    self.assertEqual(txt[1], './temp/b.txt')
    self.assertEqual(txt[2], './temp/c.txt')
    self.assertEqual(txt[3], './temp/d.txt')
    self.assertEqual(py[0], './temp/1.py')
    self.assertEqual(py[1], './temp/2.py')
    self.assertEqual(py[2], './temp/3.py')




  def test_data_xml(self):
    input = '''
      <joe attr1="abc" attr2="3" attr4="true">
        <node n="aaa" m="bbb">this is test</node>
        <node>
          i'm joe
        </node>
        <child a="a">child text</child>
      </joe>
      '''
    m = data_xml(input)
    self.assertEqual(m.tag, 'joe')
    self.assertEqual(m.attrs['attr1'], 'abc')
    self.assertEqual(m.attrs['attr2'], '3')
    self.assertEqual(m.attrs['attr4'], 'true')
    self.assertEqual(m.node[0].attrs['n'], 'aaa')
    self.assertEqual(m.node[0].attrs['m'], 'bbb')
    self.assertEqual(m.node[0].text, 'this is test')
    self.assertEqual(m.node[1].text.strip(), 'i\'m joe')
    self.assertEqual(m.child.attrs['a'], 'a')
    self.assertEqual(m.child.text, 'child text')
    self.assertEqual(m.childs[2].text, 'child text')

  def test_data_json(self):
    input = '''
      {
        "num"  : 1234,
        "bool" : true,
        "array": ["str", 123, true],
        "dic"  : {
                  "key1": "val1",
                  "key2": "val2"
                 }
      }
      '''
    m = data_json(input)
    self.assertEqual(m['num'], 1234)
    self.assertEqual(m['bool'], True)
    self.assertEqual(len(m['array']), 3)
    self.assertEqual(m['array'][0], 'str')
    self.assertEqual(m['array'][1], 123)
    self.assertEqual(m['array'][2], True)
    self.assertEqual(m['dic']['key1'], 'val1')
    self.assertEqual(m['dic']['key2'], 'val2')

  def test_data_ini(self):
    input = '''
[sec1]
a = 123
b = ab
c = ['a','b']
d = {'aa':1,'bb':true,'cc':'haha'}
 
[sec2]
e = 34
f = ff
g = fsafdsa
'''
    m = data_ini(input)
    self.assertEqual(m['sec1']['a'], '123')
    self.assertEqual(m['sec1']['b'], 'ab')
    self.assertEqual(m['sec1']['c'], "['a','b']")
    self.assertEqual(m['sec1']['d'], "{'aa':1,'bb':true,'cc':'haha'}")
    self.assertEqual(m['sec2']['e'], '34')
    self.assertEqual(m['sec2']['f'], 'ff')
    self.assertEqual(m['sec2']['g'], 'fsafdsa')


if __name__ == '__main__':
  pass
  #unittest.main()