import os
import json
import configparser
import xml.dom.minidom
import sqlite3
from collections import OrderedDict


def file_path(file):
  return os.path.dirname(os.path.realpath(file))


def file_openw(file, encoding='utf-8'):
  path_create(file_path(file))
  fh = open(file, 'w', encoding=encoding)
  return fh


def file_create(file, encoding='utf-8'):
  path_create(file_path(file))
  with open(file, 'w', encoding=encoding) as fh:
    pass


def file_exists(file):
  return os.path.isfile(file)


def file_delete(file):
  os.remove(file)


def file_read(file, encoding='utf-8'):
  with open(file, 'r', newline='\n', encoding=encoding) as fh:
    return fh.read()


def file_write_all(file, data, encoding='utf-8'):
  path_create(file_path(file))
  with open(file, 'w', newline='\n', encoding=encoding) as fh:
    fh.write(data)


def path_create(path):
  os.makedirs(path, exist_ok=True)


def path_exists(path):
  return os.path.exists(path)


def path_delete(path):
  import shutil
  shutil.rmtree(path, ignore_errors=True)

def path_files(path, pattern):
  import glob
  ret = []
  if not (path.endswith('/') or path.endswith('\\')):
    path = path + '/'

  for f in glob.glob(path + pattern):
    ret.append(f.replace('\\', '/'))

  return ret




def data_read(txt):
  if file_exists(txt):
    return file_read(txt)
  else:
    return txt

def data_json(json_input):
  text = data_read(json_input)
  return json.loads(text, object_pairs_hook=OrderedDict)

def data_ini(ini_input):
  ret = OrderedDict([])
  config = configparser.ConfigParser(inline_comment_prefixes=';')
  if file_exists(ini_input):
    config.read_file(ini_input)
  else:
    config.read_string(ini_input)
  for sec_name in config.sections():
    sec = OrderedDict([])
    for opt_name, opt_val in config.items(sec_name):
      sec[opt_name] = opt_val
    ret[sec_name] = sec
  return ret

def data_sqlite3_table(sql_file, sql_query):
  with sqlite3.connect(sql_file) as conn:
    c = conn.cursor()
    execute_ret = c.execute("SELECT id, name  from controls")
    ret = []
    for row in execute_ret:
      ret.append(row)
    return ret
def data_xml(xml_input):
  if file_exists(xml_input):
    domTree = xml.dom.minidom.parse(xml_input)
  else:
    domTree = xml.dom.minidom.parseString(xml_input)
  element = domTree.documentElement
  return _xml2Dic(element)


def _xml2Dic(element):
  ret = OrderedDict([])
  ret['name']  = element.tagName
  ret['attrs'] = OrderedDict([])
  ret['childs']= []
  ret['text']  = None

  for key, val in element.attributes.items():
    ret['attrs'][key] = val

  txt = ''
  for child in element.childNodes:
    if isinstance(child, xml.dom.minidom.Element):
      ret['childs'].append(_xml2Dic(child))
    elif isinstance(child, xml.dom.minidom.Text):
      txt += child.wholeText

  if len(ret['childs']) == 0:
    ret['text'] = txt
  return ret
