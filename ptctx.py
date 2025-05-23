import collections
import os
import ptutil
import inspect

LOG_ERROR = 0
LOG_INFO  = 1
LOG_DEBUG = 2

class PT:
  @staticmethod
  def execute(argv):
    usage = '''
python pt <template> [options] 
options：
  -nologo                 Suppress the display of the logo.
  -nocosttime             Do not show execution time.
  -out  <file>            Specify the output file, otherwise the output will be written to stdout.
  -ext  <path>            Specify a Python file or a directory containing Python files for extension.
  -args <dict>            Define variables using a Python dictionary.
  -ini  <name=file>       Load variables from an INI file.
  -json <name=file>       Load variables from a JSON file.
  -xml  <name=file>       Load variables from an XML file.
  -yaml <name=file>       Load variables from a YAML file.
  -kv   <name=file>       Load variables from a Key-Value file.
  -sql  <name=file,query> Load variables from a SQLite file.
  -log  <level>           Set log level:
                            0 - ERROR
                            1 - INFO (default)
                            2 - DEBUG
'''

    try:
      argc = len(argv)
      if (argc < 2):
        print('ERROR: Please input "<template>".')
        print(usage)
        return

      template_file = argv[1]
      if not ptutil.file_exists(template_file):
        print('ERROR: Can not find template file "' + template_file + '".')
        print(usage)
        return

      # import all functions in ptutils into globals(), so they can be used in the template.
      for fname, obj in inspect.getmembers(ptutil, inspect.isfunction):
        if not fname.startswith('_'):
          globals()[fname] = obj

      ctx = _PTCtx(template_file)

      if argc > 2:
        if argc % 2 != 0:
          print('Wrong arguments list.')
          print(usage)
          return
        # Set the log level first, then process the -out parameter using the appropriate log level.
        if '-log' in argv:
          ctx.log_level = int(argv[argv.index('-log') + 1])

        for i in range(2, argc, 2):
          option, val = argv[i], argv[i + 1]

          if option == '-out':
            ctx.output_file(val, True)
          elif option == '-args':
            ctx.variables(eval(val))
          elif option == '-ini':
            name, ini_file = PT._split_name_value(val)
            ctx.variables({name: ptutil.data_ini(ini_file)})
          elif option == '-json':
            name, json_file = PT._split_name_value(val)
            ctx.variables({name: ptutil.data_json(json_file)})
          elif option == '-xml':
            name, xml_file = PT._split_name_value(val)
            ctx.variables( {name: ptutil.data_xml(xml_file)} )
          elif option == '-yaml':
            name, yaml_file = PT._split_name_value(val)
            ctx.variables( {name: ptutil.data_yaml(yaml_file)} )
          elif option == '-kv':
            name, kv_file = PT._split_name_value(val)
            ctx.variables( {name: ptutil.data_KV(kv_file)} )
          elif option == '-sql':
            name, sql_val = PT._split_name_value(val)
            sql_file, sql_query = PT._split_name_value(sql_val, ',')
            ctx.variables({name: ptutil.data_sqlite(sql_file, sql_query)})
          elif option == '-ext':
            ctx.extension(val, True)
          elif option == '-log':
            ctx.log_level = int(val)
          else:
            raise SyntaxError('Invalid option "%s".' % option)
      out_text = ctx.eval()
      if out_text: print(out_text)

    except Exception as err:
      print(str(err))
      print(usage)

  @staticmethod
  def eval(template, args={}, output_file=None, debug=False):
    ctx = _PTCtx(template, args, output_file)
    if debug:
      ctx.log_level = LOG_DEBUG
    return ctx.eval()

  @staticmethod
  def _split_name_value(val, sep='='):
    pos = val.find(sep)
    if pos < 0:
      raise SyntaxError(f'Can not find name separator "{sep}" in "{val}".')
    return val[0:pos].strip(), val[pos + 1:].strip()

class _PTCtx:
  def __init__(self, template, args={}, output_file=None):
    self._template = template
    self._output = ''
    self._output_file = output_file
    self._output_file_hd = None
    try:
      if output_file is not None:
        self._output_file_hd = ptutil.file_openw(self._output_file)
    except Exception as ex:
      self._log(LOG_ERROR, 'File to open output file "' + self._output_file + '": ' + str(ex))
    self._code = ''
    self._g = globals().copy()
    self._l = locals().copy()
    self._l['ctx'] = self
    if args: self._l.update(args)

    self.TAB = '  '
    self._depth = 0
    self._exprs = {}
    self._parent = None
    self._output_indent = True
    self._indent = ''
    self._log_level = 1  # 0-ERROR 1-INFO 2-DEBUG

  @property
  def code(self):
    return self._code

  def close(self):
    if self._output_file_hd is not None:
      self._output_file_hd.close()
      self._output_file_hd = None
      self._output_file = ''

  def variables(self, vars):
    assert type(vars) is dict, 'The variables must be a dictionary.'
    self._l.update(vars)

  def output_file(self, file, ignore_template=False):
    if self._output_file_hd is not None:
      self._output_file_hd.close()
      self._output_file_hd = None
      self._output_file = ''
    self._output_file = file
    self._output_file_hd = None
    if self._output_file is not None and self._output_file != '':
      real_file = self._absolute_file(self._output_file, ignore_template)
      try:
        self._output_file_hd = ptutil.file_openw(real_file)
        self._log(LOG_INFO, "Generate file: " + real_file)
      except Exception as ex:
        self._log(LOG_ERROR, 'File to open file "' + real_file + '": ' + str(ex))

  @property
  def log_level(self):
    return self._log_level

  @log_level.setter
  def log_level(self, val):
    self._log_level = val

  def eval(self):
    self._translate()
    self._log(LOG_DEBUG, '======Code=====\r\n' + self.add_line_NO(self._code))
    self._g.update(self._l)
    self._g['OrderedDict'] = collections.OrderedDict
    exec(self._code, self._g)
    return self._output

  def add_line_NO(self, code):
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    lines = code.split('\n')
    for i in range(len(lines)):
      stri = str(i+1).ljust(5)
      lines[i] = stri + lines[i]
    return os.linesep.join(lines)

  def output(self, str):
    indent = self.indent_str()
    if indent != '':
      if self._output_indent:
        self.output_raw(indent)
        self._output_indent = False
      if str.endswith('\n'):
        str = str[0:-1]
        self._output_indent = True
      if str.find('\n') >= 0:
        str = str.replace('\n', '\n' + indent)
      if self._output_indent:
        str = str + '\n'
      self.output_raw(str)
    else:
      self.output_raw(str)

  def output_exp(self, exp_str):
    expr = self._exprs[exp_str]
    ret = self._eval_expr(expr, self._g, self._l)
    self.output(str(ret))

  def extension(self, py_file, ignore_template=False):
    real_path = self._absolute_file(py_file, ignore_template)
    self._log(LOG_DEBUG, 'Extension file \'' + real_path + '\'')
    if ptutil.file_exists(real_path) and real_path.endswith('.py'):
      with open(real_path, 'rb') as fh:
        try:
          exec(fh.read(), self._g)
          self._log(LOG_INFO, 'Extension file \'' + real_path + '\' load successfully.')
        except Exception as ex:
          self._log(LOG_ERROR, 'Failed to load extension file "' + py_file + '": ' + str(ex))
    elif ptutil.path_exists(real_path):
      fs = ptutil.path_files(real_path, '*.py')
      for f in fs:
        with open(f, 'rb') as fh:
          try:
            exec(fh.read(), self._g)
            self._log(LOG_INFO, 'Extension file \'' + f + '\' load successfully.')
          except Exception as ex:
            self._log(LOG_ERROR, 'Failed to load extension file "' + f + '": ' + str(ex))
    else:
      self._log(LOG_ERROR, 'Invalid extension \'' + real_path + '\'')


  def include(self, pt_file, args, offset):
    real_path = self._absolute_file(pt_file)
    ctx = _PTCtx(real_path, args, None)
    ctx._parent = self
    ctx._indent = ' ' * offset
    ctx.eval()

  def add_indent(self):
    self._indent += '  '

  def remove_indent(self):
    if len(self._indent) >= 2:
      self._indent = self._indent[0:-2]

  def indent_str(self):
    if self._parent is not None:
      return self._parent.indent_str() + self._indent
    else:
      return self._indent

  def output_raw(self, str):
    if self._parent is not None:
      self._parent.output_raw(str)
    else:
      if self._output_file_hd is not None:
        self._output_file_hd.write(str)
      else:
        self._output += str

  def _translate(self):
    self._depth = 0
    tokenizer = Tokenizer(self._template)
    code_stack = []

    while True:
      line = tokenizer.next_line()
      if line is None:
        break
      if line.type == 'text':
        self._on_text_(line.text)
      elif line.type == 'expr':
        self._exprs[line.text] = line  # Cache the expression, it will be used when eval the expression
        self._on_expr_(line.text)
      elif line.type == 'code':
        if line.is_blank:
          continue
        code = line.text
        if line.is_single_line_code:
          first_word = line.first_word
          if first_word in ['for', 'if', 'while']:
            if first_word == 'for':
              self._on_code_(f'{line.words[1]}_idx = -1')
            code_stack.append(line)
            if not code.endswith(':'): code += ':'
            self._on_code_(code.lstrip())
            self._depth += 1
            if first_word == 'for':
              self._on_code_(f'{line.words[1]}_idx += 1')
          elif first_word in ['elif', 'else']:
            if len(code_stack) == 0 or code_stack[-1].first_word != 'if':
              raise SyntaxError('\'' + first_word + '\' must match \'if\'')
            if not code.endswith(':'): code += ':'
            self._depth -= 1
            self._on_code_(code)
            self._depth += 1
          elif first_word in ['endfor', 'endif', 'endwhile']:
            if len(code_stack) == 0 or code_stack[-1].first_word != first_word[3:]:
              raise SyntaxError('\'' + first_word + '\' must match \'' + first_word[3:] + '\'')
            code_stack.pop(-1)
            self._depth -= 1
          elif first_word in ['@include', '@output_file', '@extension', '@indent+', '@indent-']:
            out_code = 'ctx.' + code[1:] #remove @
            if first_word == '@include':
              out_code = out_code.rstrip(' \t')
              assert(out_code[-1] == ')')
              # Append line offset into the 'include' parameter list
              out_code = out_code[0:-1] + ', ' + str(line.code_offset) + ')'
            elif first_word == '@indent+':
              out_code = 'ctx.add_indent()'
            elif first_word == '@indent-':
              out_code = 'ctx.remove_indent()'
            self._on_code_(out_code)
          else:
            self._on_code_(code)
        else:
          self._on_code_(code)
    self._on_code_('ctx.close()')

  def _on_text_(self, line):
    self._print_(self.TAB * self._depth + 'ctx.output(' + repr(line) + ')')

  def _on_expr_(self, line):
    self._print_(self.TAB * self._depth + 'ctx.output_exp(' + repr(line) + ')')

  def _on_code_(self, line):
    self._print_(self.TAB * self._depth + line)

  def _absolute_file(self, file, ignore_template=False):
    if os.path.isfile(self._template) and not ignore_template:
      current_path = os.path.dirname(os.path.realpath(self._template))
    else:
      current_path = os.getcwd()
    return os.path.abspath(os.path.join(current_path, file))

  def _print_(self, code):
    if not code[-1] in '\r\n':
      code += os.linesep
    self._code += code

  def _eval_expr(self, expr_block, gg, ll):
    g = gg
    l = ll.copy()
    expr_block = expr_block.copy()
    filters = expr_block.expr_filters()
    if filters is not None:
      l['__pt_expr_self__'] = self._eval_expr(filters[0], g, l)
      for i in range(1, len(filters)):
        if filters[i].token_count == 1 and callable(eval(filters[i].text, g, l)):
          filters[i].expr_append_self()
        l['__pt_expr_self__'] = self._eval_expr(filters[i], g, l, )
      return l['__pt_expr_self__']

    ternary = expr_block.expr_ternary()
    if ternary is not None:
      if self._eval_expr(ternary[0], g, l):
        return self._eval_expr(ternary[1], g, l)
      else:
        return self._eval_expr(ternary[2], g, l)

    toks = []
    expr_block.expr_reset()
    next_tok = expr_block.expr_next()
    while next_tok is not None:
      if next_tok[0].text in ['(', '[', '{']:
        sub_block = _Block(next_tok, 'expr')
        subs = sub_block.expr_subs()
        txt = ''
        for sub in subs:
          if sub.text in ['(', '[', '{', ')', ']', '}', ',', ':']:
            txt += sub.text
          else:
            val_name = self._find_var_name(l)
            l[val_name] = self._eval_expr(sub, g, l)
            txt += val_name
        next_tok = [_Token(txt, 0, 0)]
      if next_tok[0].text == 'self':
        next_tok[0].text = '__pt_expr_self__'

      toks += next_tok
      next_tok = expr_block.expr_next()

    pos, cnt = 0, len(toks)
    while pos < cnt:
      tok = toks[pos]
      if tok.is_name and pos + 2 < cnt and toks[pos+1].text == '.' and toks[pos+2].is_name:
        ret_var_name = self._eval_prp(tok.text, toks[pos+2].text, g, l)
        if ret_var_name is not None:
          toks[pos+2].text = ret_var_name
          toks[pos].text = ''
          toks[pos+1].text = ''
          pos = pos + 2
        else:
          pos = pos + 2
          while pos < cnt and pos + 2 < cnt and toks[pos+1].text == '.' and toks[pos+2].is_name:
            pos = pos + 2
        continue

      pos += 1
    expr_txt = ''
    for tok in toks:
      expr_txt += tok.text
    try:
      return eval(expr_txt, g, l)
    except Exception as ex:
      self._log(LOG_ERROR, 'Failed to eval expression: \'' + expr_txt + '\' [' + repr(ex) + ']')

  def _eval_prp(self, name, prp, g, l):
    #if prp in l or prp in g:   # support the property name is a variable but not a string.
    #  prp = eval(prp, g, l)
    try:
      val = eval(name, g, l)
    except NameError:
      return None

    val1 = None
    if hasattr(val, prp):
      val1 = eval('val.' + prp)
      if callable(val1):
        val1 = None
    if val1 is None:
      try:
        val1 = eval('val[' + repr(prp) + ']')
      except Exception as ex:
        return None
    result_name = self._find_var_name(l)
    l[result_name] = val1
    return result_name

  def _find_var_name(self, l):
    i = 0
    while True:
      name = '___mid_var_' + str(i) + '___'
      if name in l:
        i += 1
      else:
        break
    return name

  def _log(self, level, msg):
    if level > self._log_level: return
    if level == LOG_ERROR: print('[ERROR]', msg)
    if level == LOG_INFO:  print('[INFO ]', msg)
    if level == LOG_DEBUG: print('[DEBUG]', msg)



class Tokenizer:
  def __init__(self, data):
    self._text = data
    self._path = os.path.curdir
    if os.path.isfile(data):
      self._path = os.path.dirname(data)
      with open(data, 'r') as fh:
        self._text = fh.read()

    self._line = 0
    self._offset = 0
    self._pos = 0
    self._end = len(self._text)

    self._lines = None
    self._state = 'text'
    self._code_offset = 0

  @property
  def line(self):
    return self._line

  @property
  def offset(self):
    return self._offset

  @property
  def file_path(self):
    return self._path

  def next_tok(self,
               process_string=True,
               process_c_comments=False,
               process_python_comments=True,
               custom_toks=[]):  # custom_toks must be single line token
    if __debug__:
      for ctok in custom_toks:
        if '\r' in ctok or '\n' in ctok:
          raise AssertionError('CR,LF can not appear in the custom tokens parameter.')

    line,offset = self._line, self._offset
    pos = self._pos
    if pos >= self._end:
      return None

    ch = self._text[pos]

    for cus_tok in custom_toks:
      cus_len = len(cus_tok)
      if ch == cus_tok[0] and pos + cus_len <= self._end and cus_tok == self._text[pos:pos + cus_len]:
        self._pos += cus_len
        self._offset += cus_len
        return _Token(cus_tok, line, offset)

    if ch == '\n':
      pass
    elif ch == '\r':
      if pos + 1 < self._end and self._text[pos + 1] == '\n':
        pos = pos + 1
    elif ch in ['\t', ' ']:
      while pos + 1 < self._end and self._text[pos + 1] in ['\t', ' ']:
        pos = pos + 1
    elif '0' <= ch <= '9':
      while pos + 1 < self._end and '0' <= self._text[pos + 1] <= '9':
        pos = pos + 1
    elif ch == '_' or ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
      while pos + 1 < self._end and (('0' <= self._text[pos + 1] <= '9') or
                                     ('a' <= self._text[pos + 1] <= 'z') or
                                     ('A' <= self._text[pos + 1] <= 'Z') or
                                     self._text[pos + 1] == '_'):
        pos = pos + 1

    elif ch == '/' and pos + 1 < self._end and self._text[pos + 1] == '/' and process_c_comments:
      return self._fetch_line_comments()
    elif ch == '/' and pos + 1 < self._end and self._text[pos + 1] == '*' and process_c_comments:
      return self._fetch_block_comments()
    elif ch == '#' and process_python_comments:
      return self._fetch_line_comments('#')
    elif ch in ['"', '\''] and pos + 2 < self._end and self._text[pos:pos + 3] in ['"""',"'''"] and process_python_comments:
      return self._fetch_block_comments(self._text[pos:pos + 3], self._text[pos:pos + 3])
    elif ch in ['"', '\''] and process_string:
      return self._fetch_string()
    else:
      pass

    tok = self._text[self._pos:pos + 1]
    self._pos = pos + 1
    if tok[-1] in '\r\n':
      self._offset = 0
      self._line = self._line + 1
    else:
      self._offset = self._offset + len(tok)
    return _Token(tok, line, offset)

  def _fetch_string(self):
    ch, line, offset = self._text[self._pos], self._line, self._offset
    pos = self._pos + 1
    while pos < self._end:
      next_ch = self._text[pos]
      if next_ch == ch:
        break
      elif next_ch == '\\':
        pos = pos + 1
      pos = pos + 1
    if pos >= self._end:
      raise SyntaxError('Invalid string at position line %d, offset %d.' % (self._line, self._offset))
    pos = pos + 1
    tok = self._text[self._pos:pos]
    self._pos = pos
    self._offset = self._offset + len(tok)
    return _Token(tok,line,offset)

  def _fetch_block_comments(self, comments_start='/*', comments_end='*/'):
    clen = len(comments_end)
    line, offset = self._line, self._offset
    pos = self._pos + len(comments_start)
    self._offset += len(comments_start)
    find_end = False
    while pos < self._end:
      ch = self._text[pos]
      if ch == '\n':
        self._offset = 0
        self._line += 1
        pos += 1
      elif ch == '\r' and (pos + 1 >= self._end or self._text[pos + 1] != '\n'):
        self._offset = 0
        self._line += 1
        pos += 1
      elif ch == comments_end[0] and pos + clen - 1 < self._end and self._text[pos:pos + clen] == comments_end:
        pos += clen
        self._offset += clen
        find_end = True
        break
      else:
        self._offset += 1
        pos += 1

    if not find_end:
      raise SyntaxError("Invalid block comments at line %d, offset %d" % (line, offset))
    tok = self._text[self._pos:pos]
    self._pos = pos
    return _Token(tok, line, offset)

  def _fetch_line_comments(self, comments_symbol='//'):
    line, offset = self._line, self._offset
    pos = self._pos + len(comments_symbol)
    while pos < self._end:
      if self._text[pos] == '\n':
        break
      elif self._text[pos] == '\r' and (pos + 1 >= self._end or self._text[pos + 1] != '\n'):
        break
      else:
        pos = pos + 1
    tok = self._text[self._pos:pos]
    self._pos = pos
    self._offset = self._offset + len(tok)
    return _Token(tok, line, offset)

  def _init_lines(self):
    self._lines = []
    while True:
      if self._state == 'text':
        line = self._next_text_line()
        if line is None:
          break
        # 1. Ignore the empty line(0 tokens)
        if line.is_empty:
          continue
        self._lines.append(line)
      elif self._state == 'code':
        self._lines.extend(self._parse_code_lines())
      elif self._state == 'expr':
        expr_block = self._parse_expr()
        self._lines.append(expr_block)
      else:
        raise AssertionError("Impossible go here")
    line_count = len(self._lines)

    # remove some useless blanks at the start/end of the line
    i = 0
    to_remove_blanks = []
    while i < line_count:
      if self._lines[i].type == 'code' or self._lines[i].type == 'expr':
        i = self._remove_blank_line(i, line_count, to_remove_blanks)
      else:
        i += 1
    for line_NO in to_remove_blanks:
      self._lines[line_NO] = None

  def _remove_blank_line(self, i, line_count, to_remove_blanks):
    retI = i+1
    line = self._lines[i]
    pre_line  = self._lines[i-1] if i > 0 else None
    next_line = self._lines[retI] if retI < line_count else None
    last_code = line

    # for multiple lines code, skip all code lines
    if line.type == 'code':
      while next_line is not None and next_line.type == "code":
        retI += 1
        last_code = next_line
        next_line = self._lines[retI] if retI < line_count else None

    if line.remove_head_blank == '' or line.remove_tail_blank == '':
      pre = pre_line
      if pre_line is not None and pre_line.is_blank:
        pre = self._lines[i-2] if i > 1 else None
      next = next_line
      if next_line is not None and next_line.is_blank:
        next = self._lines[retI+1] if retI+1 < line_count else None
      if (pre is None or pre.line_begin < line.line_begin) and (next is None or next.line_begin > line.line_end):
        if line.remove_head_blank == '':
          if pre_line is not None and pre_line.line_begin == line.line_begin and pre_line.is_blank:
            line.remove_head_blank = '-'
          else:
            line.remove_head_blank = '+'
        if line.remove_tail_blank == '':
          if next_line is not None and next_line.line_begin >= last_code.line_end and next_line.is_blank:
            line.remove_tail_blank = '-'
          else:
            line.remove_tail_blank = '+'

    if line.remove_head_blank == '-' and pre_line is not None and pre_line.is_blank and pre_line.line_begin == line.line_begin:
      to_remove_blanks.append(i-1)
    if line.remove_tail_blank == '-' and next_line is not None and next_line.is_blank and next_line.line_begin >= last_code.line_end:
      to_remove_blanks.append(retI)
      retI += 1

    return retI



  def next_line(self):
    if self._lines is None:
      self._init_lines()
    while len(self._lines) > 0:
      if self._lines[0] is None:
        self._lines.pop(0)
        continue
      return self._lines.pop(0)


  def _next_text_line(self):
    if self._pos >= self._end:
      return None
    toks = []
    while True:
      tok = self.next_tok(process_string=False, process_c_comments=False, process_python_comments=False, custom_toks=['{{', '{%'])
      if tok is None:
        break
      elif tok.text == '{{':
        self._state = 'expr'
        break
      elif tok.text == '{%':
        self._state = 'code'
        self._code_offset = tok.offset
        break

      toks.append(tok)
      if tok.is_newline:
        break
    return _Block(toks, 'text')

  def _parse_code_lines(self):
    lines = []
    line = []
    tok = None
    rm_head_blank = ''
    rm_tail_blank = ''

    # 1. Parse code into lines
    while True:
      pre_tok = tok
      tok = self.next_tok(custom_toks=['%}'])
      if tok is None:
        raise SyntaxError("The code block is not completed at line %d." % self._line)

      if tok.text == '%}':
        if pre_tok is not None and pre_tok.text in ['-', '+']:
          rm_tail_blank = pre_tok.text
        self._state = 'text'
        break

      # Process the first token
      if pre_tok is None:
        if tok.text in ['-', '+']:
          rm_head_blank = tok.text
          tok.text = ' '

        if tok.offset > 0:
          if tok.is_blank:
            tok = _Token(' ' * tok.offset + tok.text, tok.line, 0)
          else:
            line.append(_Token(' ' * tok.offset, tok.line, 0))
      line.append(tok)

      if tok.is_newline:
        lines.append(_Block(line, 'code'))
        line = []
    # end while

    if len(line) > 0:
      lines.append(_Block(line, 'code'))
    else:
      # the line only has "%}", insert a blank for it, so that we can remove CRLF correctly
      line.append(_Token(' ', tok.line, tok.offset))
      lines.append(_Block(line, 'code'))

    if len(lines) > 0:
      lines[0].remove_head_blank = rm_head_blank
      lines[-1].remove_tail_blank = rm_tail_blank

    # 2. Trim leading blanks for every code line
    min_blank_len = 0xFFFF
    blank_line_count = 0
    for line in lines:
      if line.is_blank:
        blank_line_count += 1
        continue
      if line.is_comments:
        continue
      if line.blank_len < min_blank_len:
        min_blank_len = line.blank_len

    is_single_line = (len(lines) - blank_line_count) == 1
    for line in lines:
      if line.is_blank:
        continue
      line.trim_blank(min_blank_len)
      if is_single_line:
        line.trim_end()
        line.is_single_line_code = True
        line.code_offset = self._code_offset
    return lines


  def _parse_expr(self):
    toks = []
    while True:
      tok = self.next_tok(custom_toks=['}}'])
      if tok is None:
        raise SyntaxError("The expression is not completed at line %d." % self._line)
      txt = tok.text
      if txt.startswith('#'):
        raise SyntaxError("The comments '%s' can not appear in the expression '%s'." % (tok, self._line))
      elif txt.startswith('"""') or txt.startswith("'''"):
        raise SyntaxError("The comments '%s' can not appear in the expression at line %d." % (tok, self._line))
      elif tok.is_newline:
        raise SyntaxError("The CR, LF can not appear in the expression at line %d." % (self._line))
      elif txt == '}}':
        self._state = 'text'
        break
      else:
        toks.append(tok)
    # Check blank-removing identifier
    rm_head_blank = '+'
    rm_tail_blank = '+'
    if len(toks) > 0 and toks[0].text == '-':
      rm_head_blank = '-'
      del toks[0]
    if len(toks) > 0 and toks[-1].text == '-':
      rm_tail_blank = '-'
      del toks[-1]

    # remove empty blank
    ret = []
    tok_count = len(toks)
    for i in range(tok_count):
      if toks[i].is_blank:
        if (i > 0 and toks[i-1].is_keyword) or (i+1 < tok_count and toks[i+1].is_keyword):
          ret.append(toks[i])
        else:
          pass
      else:
        ret.append(toks[i])
    expr = _Block(ret, 'expr')
    expr.remove_head_blank = rm_head_blank
    expr.remove_tail_blank = rm_tail_blank
    return expr

class _Token:
  def __init__(self, text, line=-1, offset=-1):
    self._text = text
    self._line = line
    self._offset = offset

  def copy(self):
    t = _Token(self.text, self._line, self._offset)
    return t

  def __str__(self):
    return self._text

  @property
  def text(self):
    return self._text

  @text.setter
  def text(self, val):
    self._text = val

  @property
  def length(self):
    return len(self._text)

  @property
  def line(self):
    return self._line

  @property
  def offset(self):
    return self._offset

  @property
  def is_number(self):
    ch = self._text[0]
    return '0' <= ch <= '9'

  @property
  def is_name(self):
    ch = self._text[0]
    return ch == '_' or ('a' <= ch <= 'z') or ('A' <= ch <= 'Z')

  @property
  def is_str(self):
    ch = self._text[0]
    return ch == '\'' or ch == '"'

  @property
  def is_newline(self):
    ch = self._text[0]
    return ch == '\r' or ch == '\n'

  @property
  def is_blank(self):
    ch = self._text[0]
    return ch == ' ' or ch == '\t'

  @property
  def is_blank_or_newline(self):
    return self.is_blank or self.is_newline

  @property
  def is_keyword(self):
    return self._text in ['and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
                          'False', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
                          'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield']

class _Block:
  def __init__(self, tokens, block_type):
    assert type(tokens) is list, 'tokens must be _Token list'
    assert block_type in ['text', 'code', 'expr'], 'type must be one value of [\'text\', \'code\', \'expr\']'
    if __debug__:
      line = tokens[0].line if len(tokens) > 0 else -1
      for token in tokens:
        assert type(token) is _Token, 'tokens must be _Token list'
        assert line == token.line, 'all tokens must be in the same line'

    self._tokens = tokens  # _Token[]
    self._type = block_type
    self._single_line_code = False
    self._code_offset = 0
    self._expr_pos = 0
    self._remove_head_blank = ''
    self._remove_tail_blank = ''

  def __str__(self):
    return '[' + self.type + ']' + '“' + self.text + '“'

  @property
  def type(self):
    return self._type

  @property
  def is_single_line_code(self):
    return self._single_line_code

  @is_single_line_code.setter
  def is_single_line_code(self, value):
    assert(type(value) is bool)
    self._single_line_code = value

  @property
  def code_offset(self):
    return self._code_offset

  @code_offset.setter
  def code_offset(self, value):
    self._code_offset = value

  @property
  def is_empty(self):
    return len(self._tokens) == 0
  @property
  def line_begin(self):
    if len(self._tokens) == 0:
      return -1
    else:
      return self._tokens[0].line

  @property
  def line_end(self):
    if len(self._tokens) == 0:
      return -1
    else:
      return self._tokens[-1].line

  @property
  def offset_start(self):
    if len(self._tokens) == 0:
      return -1
    else:
      return self._tokens[0].offset

  @property
  def text(self):
    txt = ''
    for tok in self._tokens:
      txt += tok.text
    return txt

  @property
  def length(self):
    l = 0
    for tok in self._tokens:
      l += tok.length
    return l

  @property
  def is_blank(self):
    for tok in self._tokens:
      if tok.is_blank_or_newline:
        continue
      else:
        return False
    return True

  @property
  def is_comments(self):
    w = self.first_word
    return w.startswith('#') or w.startswith('"""') or w.startswith("'''")

  @property
  def token_count(self):
    return len(self._tokens)

  @property
  def first_word(self):
    tok_count = len(self._tokens)
    for i in range(0, tok_count):
      if self._tokens[i].is_blank_or_newline:
        continue
      # @indent+, @indent-
      if self._tokens[i].text == '@' and i + 1 < tok_count and self._tokens[i + 1].is_name:
        ret = self._tokens[i].text + self._tokens[i + 1].text
        if i + 2 < tok_count and self._tokens[i + 2].text in ['+', '-']:
          ret += self._tokens[i + 2].text
        return ret
      else:
        return self._tokens[i].text
    return ''

  @property
  def words(self):
    ret = []
    tok_count = len(self._tokens)
    for i in range(0, tok_count):
      if self._tokens[i].is_blank_or_newline:
        continue
      else:
        ret.append(self._tokens[i].text)
    return ret

  @property
  def blank_len(self):
    if len(self._tokens) > 0 and self._tokens[0].is_blank:
      return self._tokens[0].length
    return 0

  @property
  def remove_head_blank(self):
    return self._remove_head_blank

  @remove_head_blank.setter
  def remove_head_blank(self, value):
    self._remove_head_blank = value

  @property
  def remove_tail_blank(self):
    return self._remove_tail_blank

  @remove_tail_blank.setter
  def remove_tail_blank(self, value):
    self._remove_tail_blank = value

  def copy(self):
    new_toks = []
    for tok in self._tokens:
      new_toks.append(tok.copy())
    b = _Block(new_toks, self._type)
    b._single_line_code  = self._single_line_code
    b._code_offset       = self._code_offset
    b._expr_pos          = self._expr_pos
    b._remove_head_blank = self._remove_head_blank
    b._remove_tail_blank = self._remove_tail_blank
    return b


  def trim_blank(self, length):
    assert length >= 0, 'length must be positive (>0).'
    if length == 0:
      return
    blen = self.blank_len
    if blen == 0:
      return
    elif blen < length:
      length = blen

    if blen == length:
      self._tokens.pop(0)
    elif blen > length:
      tok = self._tokens[0]
      self._tokens[0] = _Token(' ' * (blen - length), tok.line, tok.offset + length)

  def trim_end(self):
    while len(self._tokens) > 0:
      if self._tokens[-1].is_blank_or_newline:
        del self._tokens[-1]
      else:
        break
  def expr_reset(self):
    self._expr_pos = 0

  def expr_next(self, separators=None):
    ret = []
    brackets = []
    pos, count = self._expr_pos, self.token_count
    if pos >= count:
      return None
    while pos < count:
      ret.append(self._tokens[pos])
      tok_text = self._tokens[pos].text
      if tok_text in ['(', '[', '{']:
        brackets.append(tok_text)
      elif tok_text in [')', ']', '}']:
        if len(brackets) > 0 and  tok_text == {'(': ')', '[': ']', '{': '}'}[brackets[-1]]:
          brackets.pop(-1)
        else:
          raise SyntaxError('\'' + tok_text + '\' is not matched')
      if len(brackets) == 0 and ((separators is None) or (tok_text in separators)):
        if separators is not None:
          ret.pop(-1)
        pos += 1
        break
      else:
        pos += 1
    if len(brackets) > 0:
      raise SyntaxError('\'' + brackets[-1] + '\' is not matched')
    self._expr_pos = pos
    return ret

  def expr_filters(self):
    filters = []
    self.expr_reset()
    toks = self.expr_next(['|'])
    while toks is not None:
      filters.append(_Block(toks, 'expr'))
      toks = self.expr_next(['|'])
    if len(filters) == 1:
      return None
    return filters

  def expr_ternary(self):
    self.expr_reset()
    toks = self.expr_next(['?'])
    toks_true = self.expr_next([':'])
    if toks_true is None:
      return None
    toks_false = self.expr_next(['|'])
    if toks_false is None:
      return None
    others = self.expr_next(['|'])
    if others is not None:
      raise SyntaxError('Too many expression after ?:')
    return (_Block(toks, 'expr'), _Block(toks_true, 'expr'), _Block(toks_false, 'expr'))

  def expr_subs(self):
    assert self._tokens[0].text in ['(', '[', '{'], 'The expression must starts with (, [ or {'
    assert self._tokens[-1].text == {'(':')', '[':']', '{':'}'}[self._tokens[0].text], 'The brackets must be matched'

    self.expr_reset()
    first = _Block(self._tokens[0:1], 'expr')
    last  = _Block(self._tokens[-1:], 'expr')
    self._tokens.pop(0)
    self._tokens.pop(-1)
    ret = []
    while True:
      sub = self.expr_next([':', ','])
      if sub is None:
        break
      ret.append(_Block(sub, 'expr'))
      sep_pos = self._expr_pos - 1
      if self._tokens[sep_pos].text in [':', ',']:
        ret.append(_Block(self._tokens[sep_pos:sep_pos+1], 'expr'))  # separator
    ret.insert(0, first)
    ret.append(last)
    return ret

  def expr_append_self(self):
    line = -1
    offset = -1
    if len(self._tokens) > 0:
      line = self._tokens[-1].line
      offset = self._tokens[-1].offset + self._tokens[-1].length
    self._tokens.append(_Token('(',    line, offset))
    self._tokens.append(_Token('self', line, offset + 1))
    self._tokens.append(_Token(')',    line, offset + 5))