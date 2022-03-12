#-*- coding: UTF-8 -*-
import unittest
import sys
sys.path.insert(0, "../")
from ptctx import *


EXPRS_STR = '''
{{['a', 'b', 'c']|'|'.join(self)|self+'{}[]()'}}

{{'joe is a good man'|self.replace(' ', '-')}}

{% f = 'haha' %}

{{f.startswith('ha') ? ('starts with ha'|self.replace(' ', '()')) : 'not starts with ha'}}

{{'joe'.startswith('ha') ? ('starts with ha'|self.replace(' ', '()')) : ('not starts with ha' | self[1:] )}}  
  '''
class ptctx_test(unittest.TestCase):

  def test_next_tok_custom_toks(self):
    tz = Tokenizer(EXPRS_STR)
    i = 0
    while True:
      tok = tz.next_tok(custom_toks=['{{','}}','{%', '%}'])
      if tok is None:
        break
      if tok.is_blank_or_newline:
        continue
      print(i, ':', tok.text)
      i += 1
    self.assertEqual(i, 91)

  def test_next_tok(self):
    tz = Tokenizer(EXPRS_STR)
    i = 0
    while True:
      tok = tz.next_tok()
      if tok is None:
        break
      if tok.is_blank_or_newline:
        continue
      print(i, ':', tok.text)
      i += 1
    self.assertEqual(i, 101)

  def test_next_tok_comments(self):
    txt = '''
#this is a good 'dock'
#######AT########   
Hello
########### 
    '''
    tz = Tokenizer(txt)
    ret = ''
    i = 0
    while True:
      tok = tz.next_tok()
      if tok is None:
        break
      if tok.is_blank_or_newline:
        continue
      print(i, ':', tok.text)
      ret += tok.text
      i += 1
    self.assertEqual(ret, "#this is a good 'dock'#######AT########   Hello########### ")
    self.assertEqual(i, 4)

  def test_PT_eval_plain_text(self):
    template = '''
测试中文
“string"==\'\'\'    
    '''
    ret = PT.eval(template)
    print(ret)
    self.assertEqual(template, ret)

  def test_PT_eval_for(self):
    template = '''
a
   {%for i in range(0, 5)%}   
   test
   {%endfor%}   
b
    '''
    expect_ret = '''
a
   test
   test
   test
   test
   test
b
    '''
    ret = PT.eval(template)
    print(ret)
    self.assertEqual(expect_ret, ret)

  def test_PT_eval_if(self):
    template = '''
a  
   {%
     m = 'joel'
  #This is a comments
     if len(m) == 4:
       n = True
     else:
       n = False  
   %}
   {%if n%} 
   {%for i in range(0,5)%}  
   if
   {%endfor%}
   {%else%}
   else   
   {%endif%}
b
    '''
    expect_ret = '''
a  
   if
   if
   if
   if
   if
b
    '''
    ret = PT.eval(template)
    print(ret)
    self.assertEqual(expect_ret, ret)

  def test_expr(self):
    template = '''[
{%for i in range(1,101)%}
{{i}}{{(i % 10 != 0) ? ', ' : '\\n'-}}
{%endfor%}

{%
f = {'val2': 3}
t = {}
t['val1'] = f
%}
{{3 + t.val1.val2 * (7 - 1 - t.val1['val2'] | self*self) | self - 10}}

{{['a', 'b', 'c']|'|'.join(self)|self+'{}[]()'}}

{{'joe is a good man'|self.replace(' ', '-')}}

{% f = 'haha' %}
{{f.startswith('ha') ? ('starts with ha'|self.replace(' ', '()')) : 'not starts with ha'}}

{{'joe'.startswith('ha') ? ('starts with ha'|self.replace(' ', '()')) : ('not starts with ha' | self[1:] )}}
]'''

    expected_ret = '''[
1, 2, 3, 4, 5, 6, 7, 8, 9, 10
11, 12, 13, 14, 15, 16, 17, 18, 19, 20
21, 22, 23, 24, 25, 26, 27, 28, 29, 30
31, 32, 33, 34, 35, 36, 37, 38, 39, 40
41, 42, 43, 44, 45, 46, 47, 48, 49, 50
51, 52, 53, 54, 55, 56, 57, 58, 59, 60
61, 62, 63, 64, 65, 66, 67, 68, 69, 70
71, 72, 73, 74, 75, 76, 77, 78, 79, 80
81, 82, 83, 84, 85, 86, 87, 88, 89, 90
91, 92, 93, 94, 95, 96, 97, 98, 99, 100

20

a|b|c{}[]()

joe-is-a-good-man

starts()with()ha

ot starts with ha
]'''
    ret = PT.eval(template)
    self.assertEqual(ret, expected_ret)
    print(ret)

  def test_expr_1(self):
      template = '''[
  {%for i in range(0,10)%}
  {%-for j in range(1,11)%}{{i * 10 + j}}, {%endfor%}
  {%endfor%}
]'''

      expected_ret = '''[
1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 
11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 
21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 
31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 
41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 
51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 
61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 
71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 
81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 
91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 
]'''
      ret = PT.eval(template,debug=True)
      self.assertEqual(ret, expected_ret)
      print(ret)

  def test_outputfile(self):
    template = '''
    {% for i in range(1,101) %}
    {% @output_file('./test' + str(i) + '.txt') %}
    {{i}}--filename-{{'./test' + str(i) + '.txt'}}
    {%endfor%}'''
    ret = PT.eval(template)
    for i in range(1, 101):
      filename = './test' + str(i) + '.txt'
      self.assertTrue(ptutil.file_exists(filename))
      self.assertTrue(ptutil.file_read(filename), str(i) + '--filename-' + filename)
      ptutil.file_delete(filename)
    print(ret)

  def test_outputfile1(self):
    expect_page = '''<!DOCTYPE html>
<html>
    <head>
        <title>Page {{i}}</title>
    </head>
    <body>
        <p>This is page {{i}}.</p>
    </body>
</html>'''
    expect_index = '''<!DOCTYPE html>
<html>
    <head>
        <title>Index</title>
    </head>
    <body>
        <ul>
          <li><a href=".\pages\page1.html">Page 1</a></li>
          <li><a href=".\pages\page2.html">Page 2</a></li>
          <li><a href=".\pages\page3.html">Page 3</a></li>
          <li><a href=".\pages\page4.html">Page 4</a></li>
          <li><a href=".\pages\page5.html">Page 5</a></li>
          <li><a href=".\pages\page6.html">Page 6</a></li>
          <li><a href=".\pages\page7.html">Page 7</a></li>
          <li><a href=".\pages\page8.html">Page 8</a></li>
          <li><a href=".\pages\page9.html">Page 9</a></li>
          <li><a href=".\pages\page10.html">Page 10</a></li>
        </ul>
    </body>
</html>'''
    ret = PT.eval('./templates/multiple_files.pt')
    index = './templates/index.html'
    self.assertTrue(ptutil.file_exists(index))
    self.assertTrue(ptutil.file_read(index), expect_index)
    ptutil.file_delete(index)

    for i in range(1, 11):
      filename = './templates/pages/page' + str(i) + '.html'
      self.assertTrue(ptutil.file_exists(filename))
      self.assertTrue(ptutil.file_read(filename), expect_page.replace('{{i}}', str(i)))
      ptutil.file_delete(filename)
    print(ret)

  def test_extension(self):
    template = '''
{% @extension('./pyutils.py') %}
{% for i in range(1,10) %}
{{i}}--filename-{{i|convert}}
{%endfor%}'''
    ret = PT.eval(template)
    expect_ret = '''
1--filename-1
2--filename-4
3--filename-9
4--filename-16
5--filename-25
6--filename-36
7--filename-49
8--filename-64
9--filename-81
'''
    self.assertEqual(ret, expect_ret)

  def test_extension_file(self):
      ret = PT.eval('./templates/extension.pt')
      expect_ret = '''--1---1--
--2---4--
--3---9--
--4---16--
--5---25--
'''
      self.assertEqual(ret, expect_ret)

  def test_include(self):
    template = '''
{% for i in range(1,3) %}
   {% @include('./templates/num_matrix.pt', {'loop': i}) %}
{%endfor%}'''
    ret = PT.eval(template)
    expect_ret = '''
   ===1===
   1, 2, 3, 4, 5, 6, 7, 8, 9, 10
   11, 12, 13, 14, 15, 16, 17, 18, 19, 20
   21, 22, 23, 24, 25, 26, 27, 28, 29, 30
   31, 32, 33, 34, 35, 36, 37, 38, 39, 40
   41, 42, 43, 44, 45, 46, 47, 48, 49, 50
   51, 52, 53, 54, 55, 56, 57, 58, 59, 60
   61, 62, 63, 64, 65, 66, 67, 68, 69, 70
   71, 72, 73, 74, 75, 76, 77, 78, 79, 80
   81, 82, 83, 84, 85, 86, 87, 88, 89, 90
   91, 92, 93, 94, 95, 96, 97, 98, 99, 100
   
               
               a|b|c{}[]()
               
               joe-is-a-good-man
               
               
               starts()with()ha
               
               ot starts with ha
               
               ====1  haha====
   ===2===
   1, 2, 3, 4, 5, 6, 7, 8, 9, 10
   11, 12, 13, 14, 15, 16, 17, 18, 19, 20
   21, 22, 23, 24, 25, 26, 27, 28, 29, 30
   31, 32, 33, 34, 35, 36, 37, 38, 39, 40
   41, 42, 43, 44, 45, 46, 47, 48, 49, 50
   51, 52, 53, 54, 55, 56, 57, 58, 59, 60
   61, 62, 63, 64, 65, 66, 67, 68, 69, 70
   71, 72, 73, 74, 75, 76, 77, 78, 79, 80
   81, 82, 83, 84, 85, 86, 87, 88, 89, 90
   91, 92, 93, 94, 95, 96, 97, 98, 99, 100
   
               
               a|b|c{}[]()
               
               joe-is-a-good-man
               
               
               starts()with()ha
               
               ot starts with ha
               
               ====2  haha====
'''
    self.assertEqual(ret, expect_ret)

  def test_include_1(self):
    ret = PT.eval('./templates/students.pt', {'students': [{'name': 'joe', 'score': 88}, {'name': 'martin', 'score': 90}]})
    expect_ret = '''All students as follows:
==No index==
This is the first line. Print the input parameters as follows:
    a. Name : joe
    b. Score: 88
End.
This is the first line. Print the input parameters as follows:
    a. Name : martin
    b. Score: 90
End.

==With index==
== 0 ==
    This is the first line. Print the input parameters as follows:
        a. Name : joe
        b. Score: 88
    End.
== 1 ==
    This is the first line. Print the input parameters as follows:
        a. Name : martin
        b. Score: 90
    End.
'''
    self.assertEqual(ret, expect_ret)

  def test_expr_ternary(self):
    expr = '''{{(i % 10 != 0) ? ',': '\\r\\n' }}'''

    self.assertEqual(',', PT.eval(expr, {'i': 9}))
    self.assertEqual('\r\n', PT.eval(expr, {'i': 10}))


  def test_expr_filter(self):
    expr = '''{{t|self+val}}'''
    self.assertEqual('13', PT.eval(expr, {'val': 7, 't': 6}))

  def test_expr_filter_custom_func(self):
    expr = '''{{t|self+val|tt}}'''

    def tt(v):
      return v*v
    self.assertEqual('169', PT.eval(expr, {'val': 7, 't': 6, 'tt': tt}))

  def test_expr_prop(self):
    expr = '''{{3 + t.val1.val2 * (7 - 1 - t.val1['val2'] | self*self) | self - 10}}'''

    f = {'val2': 3}
    t = {'val1': f}
    self.assertEqual('20', PT.eval(expr, {'t': t}))

  def test_tokens(self):
    s = '{{abc_def  7878.89\r\n  \t  \t_abc123 \n%} 9 a \t'
    t = Tokenizer(s)
    self.assertEqual(t.next_tok().text, '{')
    self.assertEqual(t.next_tok().text, '{')
    self.assertEqual(t.next_tok().text, 'abc_def')
    self.assertEqual(t.next_tok().text, '  ')
    self.assertEqual(t.next_tok().text, '7878')
    self.assertEqual(t.next_tok().text, '.')
    self.assertEqual(t.next_tok().text, '89')
    self.assertEqual(t.next_tok().text, '\r\n')
    self.assertEqual(t.next_tok().text, '  \t  \t')
    self.assertEqual(t.next_tok().text, '_abc123')
    self.assertEqual(t.next_tok().text, ' ')
    self.assertEqual(t.next_tok().text, '\n')
    self.assertEqual(t.next_tok().text, '%')
    self.assertEqual(t.next_tok().text, '}')
    self.assertEqual(t.next_tok().text, ' ')
    self.assertEqual(t.next_tok().text, '9')
    self.assertEqual(t.next_tok().text, ' ')
    self.assertEqual(t.next_tok().text, 'a')
    self.assertEqual(t.next_tok().text, ' \t')

  def test_blanks1(self):
    template = '''
{% if False %}x{% endif -%}
test
'''
    ret = PT.eval(template)
    expect_ret = '''
test
'''
    self.assertEqual(ret, expect_ret)

  def test_blanks2(self):
    template = '''
{% if True %}x{% endif %}
test
'''
    ret = PT.eval(template)
    expect_ret = '''
x
test
'''
    self.assertEqual(ret, expect_ret)

  def test_blanks3(self):
    template = '''
    {% if False %}            
x
{% endif %}
test
'''
    ret = PT.eval(template)
    expect_ret = '''
test
'''
    self.assertEqual(ret, expect_ret)

  def test_blanks4(self):
    template = '''
    {% if True %}  
x
{% endif %}
test
'''
    ret = PT.eval(template)
    expect_ret = '''
x
test
'''
    self.assertEqual(ret, expect_ret)


  def test_blanks5(self):
    template = '''  {% if False %}  
  x
  {% endif %}  

test
'''
    ret = PT.eval(template)
    expect_ret = '''
test
'''
    self.assertEqual(ret, expect_ret)

  def test_blanks6(self):
    template = '''  {% if True %}  
  x
  {% endif %}   

test
'''
    ret = PT.eval(template)
    expect_ret = '''  x

test
'''
    self.assertEqual(ret, expect_ret)

  def test_blanks7(self):
    template = '''{% if False %}  x  
    {% endif %}    test'''
    ret = PT.eval(template)
    expect_ret = '''    test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks7_1(self):
    # '-' only trim the blank that ends with CRLF
    template = '''{% if False %}  x  
    {% endif -%}    test'''
    ret = PT.eval(template, debug=True)
    expect_ret = '''    test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks8(self):
    template = '''{% if True %}  x  
{% endif %}    test'''
    ret = PT.eval(template)
    expect_ret = '''  x  
    test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks9(self):
    template = '''test {% if False %}  x  
 {% endif %}    test'''
    ret = PT.eval(template)
    expect_ret = '''test     test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks10(self):
    template = '''test {% if True %}  x  
 {% endif %}    test'''
    ret = PT.eval(template)
    expect_ret = '''test   x  
     test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks11(self):
    template = ''' {% if False %}  x  {% endif %}    test'''
    ret = PT.eval(template)
    expect_ret = '''     test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks12(self):
    template = ''' {% if True %}  x  {% endif %}    test'''
    ret = PT.eval(template)
    expect_ret = '''   x      test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks13(self):
    template = ''' {% if True %}     {% if False %}  x
 {% endif %} 
{% endif %}

test'''
    ret = PT.eval(template)
    expect_ret = '''      
test'''
    self.assertEqual(ret, expect_ret)

  def test_blanks14(self):
    template = ''' {% if True %}     {% if False %}
  x
{% endif %} 
{% endif %}

test'''
    ret = PT.eval(template)
    expect_ret = '''      
test'''
    self.assertEqual(ret, expect_ret)