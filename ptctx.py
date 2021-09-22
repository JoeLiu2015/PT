import os
import ptutil

class PT:
  @staticmethod
  def execute(argv):
    usage = '''
Usage: python pt <template>
  -out  <output file>
  -args <python dictionary that define variables>
  -json <argname=json file>
  -xml  <argname=xml file>
  -ext  <a single python file -or- a directory that contains python files>
  -log <0-ERROR(default) 1-INFO  2-DEBUG>      
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

      ctx = _PTCtx(template_file)
      if argc > 2:
        if argc % 2 != 0:
          print('Wrong arguments list.')
          print(usage)
          return

        for i in range(2, argc, 2):
          option = argv[i]
          val = argv[i + 1]

          if option == '-out':
            ctx.output_file(val)
          elif option == '-args':
            ctx.variables(eval(val))
          elif option == '-json':
            pos = val.find('=')
            if pos < 0:
              raise SyntaxError('Can not find name separator "=" in "%s".' % val)
            name = val[0:pos].strip()
            json_file = val[pos+1:].strip()
            d = {}
            d[name] = ptutil.data_json(json_file)
            ctx.variables(d)
          elif option == '-xml':
            pos = val.find('=')
            if pos < 0:
              raise SyntaxError('Can not find name separator "=" in "%s".' % val)
            name = val[0:pos].strip()
            xml_file = val[pos+1:].strip()
            d = {}
            d[name] = ptutil.data_xml(xml_file)
            ctx.variables(d)
          elif option == '-ext':
            ctx.extension(val)
          elif option == '-log':
            ctx.log_level(int(val))
          else:
            raise SyntaxError('Invalid option "%s".' % option)
      out_text = ctx.eval()
      if out_text: print(out_text)

    except Exception as err:
      print(str(err))
      print(usage)

  @staticmethod
  def eval(template, args={}, output_file=None):
    ctx = _PTCtx(template, args, output_file)
    return ctx.eval()

LOG_ERROR = 0
LOG_INFO  = 1
LOG_DEBUG = 2
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
    self._parent_indent = ''
    self._parent_indent_output = True
    self._log_level = 0  # 0-ERROR 1-INFO 2-DEBUG

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

  def output_file(self, file):
    if self._output_file_hd is not None:
      self._output_file_hd.close()
      self._output_file_hd = None
      self._output_file = ''
    self._output_file = file
    self._output_file_hd = None
    if self._output_file is not None and self._output_file != '':
      real_file = self._absolute_file(self._output_file)
      try:
        self._output_file_hd = ptutil.file_openw(real_file)
      except Exception as ex:
        self._log(LOG_ERROR, 'File to open file "' + real_file + '": ' + str(ex))

  def log_level(self, val):
    self._log_level = val

  def eval(self):
    self._translate()
    self._log(LOG_DEBUG, '======Code=====\r\n' + self._code)
    exec(self._code, self._g, self._l)
    return self._output

  def output(self, str):
    if self._parent is not None:
      if self._parent_indent != '':
        if self._parent_indent_output:
          self._parent.output(self._parent_indent)
          self._parent_indent_output = False
        if str.endswith('\n'):
          str = str[0:-1]
          self._parent_indent_output = True
        if str.find('\n') >= 0:
          str = str.replace('\n', '\n' + self._parent_indent)
        if self._parent_indent_output:
          str = str + '\n'
        self._parent.output(str)
      else:
        self._parent.output(str)
      return

    if self._output_file_hd is not None:
      self._output_file_hd.write(str)
    else:
      self._output += str

  def output_exp(self, exp_str):
    expr = self._exprs[exp_str]
    ret = self._eval_expr(expr, self._g, self._l)
    self.output(str(ret))

  def extension(self, py_file):
    real_path = self._absolute_file(py_file)
    self._log(LOG_DEBUG, 'Extension file \'' + real_path + '\'')
    if ptutil.file_exists(real_path) and real_path.endswith('.py'):
      with open(real_path, 'rb') as fh:
        exec(fh.read(), self._g)
    elif ptutil.path_exists(real_path):
      fs = ptutil.path_files(real_path, '*.py')
      for f in fs:
        with open(f, 'rb') as fh:
          exec(fh.read(), self._g)
    else:
      self._log(LOG_ERROR, 'Invalid extension \'' + real_path + '\'')


  def include(self, pt_file, args, offset):
    real_path = self._absolute_file(pt_file)
    ctx = _PTCtx(real_path, args, None)
    ctx._parent = self
    ctx._parent_indent = ' ' * offset
    ctx.eval()

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
        code = line.text
        if line.is_single_line_code:
          first_word = line.first_word
          if first_word in ['for', 'if', 'while']:
            code_stack.append(line)
            if not code.endswith(':'): code += ':'
            self._on_code_(code)
            self._depth += 1
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
          elif first_word in ['@include', '@output_file', '@extension']:
            out_code = 'ctx.' + code[1:] #remove @
            if first_word == '@include':
              out_code = out_code.rstrip(' \t')
              assert(out_code[-1] == ')')
              # Append line offset into the 'include' parameter list
              out_code = out_code[0:-1] + ', ' + str(line.code_offset) + ')'
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

  def _absolute_file(self, file):
    if os.path.isfile(self._template):
      current_path = os.path.dirname(os.path.realpath(self._template))
    else:
      current_path = os.getcwd()
    return os.path.abspath(os.path.join(current_path, file))

  def _print_(self, code):
    if not code[-1] in '\r\n':
      code += os.linesep
    self._code += code

  def _eval_expr(self, expr_block, gg, ll):
    g = gg.copy()
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
      self._log(LOG_ERROR, 'Failed to eval expression: \'' + expr_txt + '\'')

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

    self._lines = []
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

  def next_line(self):
    while len(self._lines) == 0:
      if self._state == 'text':
        line = self._next_text_line()
        # 1. Ignore the empty line(0 tokens)
        if line is not None and line.is_empty:
          pass
        # 2. Ignore the leading blank of the code block or expr block
        elif line is not None and line.is_blank:
          if self._state == 'code':
            pass
          elif self._state == 'expr':
            expr_block = self._parse_expr()
            if not expr_block.remove_head_blank:
              self._lines.append(line)
            self._lines.append(expr_block)
          else:
            self._lines.append(line)
        else:
          self._lines.append(line)
      elif self._state == 'code':
        self._parse_code_lines()
        text = self._next_text_line()
        # Ignore the trailing blank of the code block
        if text is not None and text.is_blank:
          pass
        else:
          self._lines.append(text)
      elif self._state == 'expr':
        expr_block = self._parse_expr()
        self._lines.append(expr_block)
        if expr_block.remove_tail_blank:
          text = self._next_text_line()
          # Ignore the trailing blank of the expr block
          if text is not None and text.is_blank:
            pass
          else:
            self._lines.append(text)
      else:
        raise AssertionError("Impossible go here")
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
    first_tok, min_blank_len = None, -1

    # 1. Parse code into lines
    while True:
      tok = self.next_tok(custom_toks=['%}'])
      if tok is None or tok.text == '%}':
        self._state = 'text'
        break

      # Append blank token at the first code line
      if first_tok is None:
        first_tok = tok
        if first_tok.offset > 0:
          if first_tok.is_blank:
            tok = _Token(' ' * first_tok.offset + tok.text, tok.line, 0)
          else:
            line.append(_Token(' ' * first_tok.offset, tok.line, 0))
      line.append(tok)
      if tok.is_newline:
        line_block = _Block(line, 'code')
        lines.append(line_block)
        line = []
    if len(line) > 0:
      line_block = _Block(line, 'code')
      lines.append(line_block)

    # 2. Trim leading blanks for every code line
    min_blank_len = 0xFFFF
    blank_line_count = 0
    for line in lines:
      if line.is_blank:
        blank_line_count += 1
        continue
      cur_len, first_word = line.blank_len, line.first_word
      # Ignore comments lines
      if first_word.startswith('#') or first_word.startswith('"""') or first_word.startswith("'''"):
        cur_len = 0xFFFF
      if cur_len < min_blank_len:
        min_blank_len = cur_len

    is_single_line = (len(lines) - blank_line_count) == 1
    for line in lines:
      if line.is_blank:
        continue
      line.trim_blank(min_blank_len)
      if is_single_line:
        line.is_single_line_code = True
        line.code_offset = self._code_offset
      self._lines.append(line)


  def _parse_expr(self):
    toks = []
    while True:
      tok = self.next_tok(custom_toks=['}}'])
      if tok is None:
        raise SyntaxError("The express is not completed at lien %d." % self._line)
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
    # remove blank identify
    rm_head_blank = False
    rm_tail_blank = False
    if len(toks) > 0 and toks[0].text == '-':
      rm_head_blank = True
      toks.pop(0)
    if len(toks) > 0 and toks[-1].text == '-':
      rm_tail_blank = True
      toks.pop(-1)

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
    ch = self._text[0]
    if '0' <= ch <= '9':
      self._type = 'number'
    elif ch in [' ', '\t']:
      self._type = 'blank'
    elif ch in '\r\n':
      self._type = 'newline'
    elif ch in ['\'', '"']:
      self._type = 'string'
    elif ch == '_' or ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
      self._type = 'name'
    else:
      self._type = ''

  def copy(self):
    t = _Token(self.text, self._line, self._offset)
    t._type = self._type
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
  def type(self):
    return self._type

  @type.setter
  def type(self, val):
    self._type = val

  @property
  def is_number(self):
    return self._type == 'number'

  @property
  def is_name(self):
    return self._type == 'name'

  @property
  def is_str(self):
    return self._type == 'string'

  @property
  def is_newline(self):
    return self._type == 'newline'

  @property
  def is_blank(self):
    return self._type == 'blank'

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
      for token in tokens:
        assert type(token) is _Token, 'tokens must be _Token list'

    self._tokens = tokens  # _Token[]
    self._type = block_type
    self._single_line_code = False
    self._code_offset = 0
    self._expr_pos = 0
    self._remove_head_blank = False
    self._remove_tail_blank = False

  def __str__(self):
    return self.text

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
  def line_count(self):
    tok_count = len(self._tokens)
    if tok_count == 0:
      return 0
    elif tok_count == 1:
      return 1
    else:
      return self._tokens[-1].line - self._tokens[0].line + 1

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
  def token_count(self):
    return len(self._tokens)

  @property
  def first_word(self):
    tok_count = len(self._tokens)
    for i in range(0, tok_count):
      if self._tokens[i].is_blank_or_newline:
        continue
      if self._tokens[i].text == '@' and i + 1 < tok_count and self._tokens[i + 1].is_name:
        return self._tokens[i].text + self._tokens[i + 1].text
      else:
        return self._tokens[i].text

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
    b = _Block([], self._type)
    b._single_line_code  = self._single_line_code
    b._code_offset       = self._code_offset
    b._expr_pos          = self._expr_pos
    b._remove_head_blank = self._remove_head_blank
    b._remove_tail_blank = self._remove_tail_blank
    for tok in self._tokens:
      b._tokens.append(tok.copy())
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
      tok0 = self._tokens[0]
      self._tokens[0] = _Token(' ' * (blen - length), tok0.line, tok0.offset + length)

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
    self._tokens.append(_Token('(', -1, -1))
    self._tokens.append(_Token('self', -1, -1))
    self._tokens.append(_Token(')', -1, -1))
