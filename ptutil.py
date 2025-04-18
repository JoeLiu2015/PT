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

def data_yaml(yaml_input):
  yaml = yaml_input
  if file_exists(yaml_input):
    yaml = file_read(yaml_input)

  lines_tmp = yaml.splitlines()
  lines = []
  spaces = []
  for line in lines_tmp:
    if len(line.strip()) == 0 or line.strip().startswith('#'):
      continue
    lines.append(line)
    spaces.append(len(line) - len(line.lstrip()))
  return _parseYamlObj(lines, spaces)

def _parseYamlObj(lines, spaces):
  if len(lines) == 0:
    return None

  has_more_levels = False
  for i in range(1, len(spaces)):
    if spaces[i] != spaces[0]:
      has_more_levels = True
      break

  if not has_more_levels:
    if ':' in lines[0]:
      obj = OrderedDict()
      for line in lines:
        if not ':' in line:
          raise ValueError('invalid key:value line - ' + line)
        key, value = line.split(':', 1)
        obj[key.strip()] = value.strip()
      return obj
    elif lines[0].lstrip().startswith('-'):
      obj = []
      for line in lines:
        if not line.lstrip().startswith('-'):
          raise ValueError('invalid array item line - ' + line)
        obj.append(line.strip()[1:])
      return obj
    else:
      raise ValueError('invalid yaml line - ' + lines[0])

  groups = OrderedDict()
  level = spaces[0]
  cnt = len(spaces)
  i = 0
  while i < cnt:
    if i + 1 >= cnt:
      groups[i] = None
      i = i + 1
      continue
    if spaces[i+1] == level:
      groups[i] = None
      i = i + 1
      continue
    if spaces[i+1] > level:
      n = i + 1
      while n < cnt:
        if spaces[n] == level:
          break
        elif spaces[n] < level:
          raise ValueError('invalid array item line - ' + lines[n])
        n = n + 1
      groups[i] = (i + 1, n)
      i = n
      continue
    raise ValueError('invalid array item line with wrong level - ' + lines[i+1])

  if lines[0].lstrip().startswith('-'):
    obj = []
    for k, v in groups.items():
      line = lines[k]
      if not line.lstrip().startswith('-'):
        raise ValueError('invalid array item line - ' + line)
      if v is None:
        obj.append(line.strip()[1:])
      else:
        if line.strip() == '-':
          obj.append(_parseYamlObj(lines[v[0]:v[1]], spaces[v[0]:v[1]]))
        else:
          new_lines = lines[(v[0]-1):v[1]]
          new_spaces = spaces[(v[0]-1):v[1]]
          new_lines[0] = new_lines[0].replace('-', ' ', 1)
          new_spaces[0] = len(new_lines[0]) - len(new_lines[0].lstrip())
          obj.append(_parseYamlObj(new_lines, new_spaces))
    return obj
  elif ':' in lines[0]:
    obj = OrderedDict()
    for k, v in groups.items():
      line = lines[k]
      if not ':' in line:
        raise ValueError('invalid key:value line - ' + line)
      key, value = line.split(':', 1)
      if v is None:
        obj[key.strip()] = value.strip()
      else:
        obj[key.strip()] = _parseYamlObj(lines[v[0]:v[1]], spaces[v[0]:v[1]])
    return obj
  else:
    raise ValueError('invalid yaml line - ' + lines[0])

def _xml2Dic(element):
  ret = OrderedDict()
  childs = []
  attrs  = OrderedDict()
  setattr(ret, 'tag',    element.tagName)
  setattr(ret, 'attrs',  attrs)
  setattr(ret, 'text',   None)
  setattr(ret, 'childs', childs)

  for key, val in element.attributes.items():
    attrs[key] = val

  txt = ''
  for child in element.childNodes:
    if isinstance(child, xml.dom.minidom.Element):
      child = _xml2Dic(child)
      childs.append(child)
      child_name = child.tag
      if hasattr(ret, child_name):
        child_obj = getattr(ret, child_name)
        if isinstance(child_obj, OrderedDict):
          setattr(ret, child_name, [child_obj, child])
        else:
          child_obj.append(child)
      else:
        setattr(ret, child_name, child)
    elif isinstance(child, xml.dom.minidom.Text):
      txt += child.wholeText

  if len(childs) == 0:
    ret.text = txt
  return ret

