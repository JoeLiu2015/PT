# PT

### 1. Overview
PT means "Python Template", it is template tool that wrote by Python language. It support two style blocks:
  
  - {% -- any python code -- %}
  - {{   -- expression --    }}


### 2. Quick Start
To use the template, we just need to write a template file or string and then execute it by PT.

**Template File (page.pt)**

```html
<!DOCTYPE html>
<html>
    <head>
        <title>{{page.title}}</title>
    </head>
    <body>
        {{page.body}}
    </body>
</html>
```

**Command**

```
python pt page.pt -out page.html -args "{'page': {'title': 'Test Page', 'body': 'Hello world'} }"
```

**Usage**

```
Usage: python pt <template>
  -out  <output file>
  -args <python dictionary that define variables>
  -ini  <argname=ini file>
  -json <argname=json file>
  -xml  <argname=xml file>
  -yaml <argname=yaml file>
  -ext  <a single python file -or- a directory that contains python files>
  -log  <0-ERROR(default) 1-INFO  2-DEBUG> 
```

### 3. Code Block
The code block is starts with '{%' and ends of '%}'. There are two kinds of code block.

#### 3.1 Built-in Code
The Built-in code must appear in the single line, the left and right blanks are ignored.

```
{% for var in var-list %}
# in the loop, the built-in variable 'var_idx'(0-based) can be used in the template
{% endfor %}

{% for key,val in var-dict %}
# in the loop, the built-in variable 'key_idx'(0-based) can be used in the template
{% endfor %}

{% while conditional-expression %}
{% endwhile %}

{% if conditional-expression %}
{% elif conditional-expression %}
{% else %}
{% endif %}

{% @output_file(file) %}  # The following text will be output to the specified file

{% @include(templatefile, args) %} # The sub-template will be included into the current template

{% @extension(py_file) %} # The py_file can be a single python file or a directory contains multiple python files

{% @indent+ %} # Add indent to every line in the following output text

{% @indent- %} # Remove the indent that added by {% @indent+ %}
```

#### 3.2 Custome Code

```
1) Single line coment:
   {% # comments %}

2) Multiple lines comments:
   {%
   '''
   comments
   comments
   '''
   %}
   
3) Normal python code (single line or multiple lines)  
   // single line code
   {% println('This is a test') %}
   
   // multiple lines code, the functions may be used in pipes
   {%
   def is_req(node):
     return ('req' not in node.attrs) or (node.attrs['req'] == '1')
     
   def desc_to_name(desc):
     desc = desc.replace('/', ' ').replace(',', ' ').replace('-', ' ').replace('&', ' ').replace('.', ' ')
     words = desc.split(' ')
     ret = ''
     for w in words:
       ret += w.capitalize()
     return ret
     any python code
   %}
```


### 4. Expression
The expression is starts with '{{' and ends with '}}'. 

  - Ternary expression
    
    Simple: {{ name.startswith('joe') ? "I'm Joe" : "I'm not Joe" }}
    
    
  - pipe
  
    ```
    The pipe symbol is '|', it can process the value that passed from previouse expression, 
    the key word 'self' means the value that passed from the previouse expression
    1) {{ 3 | self * 2 }}     The result is 6
    2) {{ 'abc' | self[1:] }} The result is 'bc'
    3) {{ ['a', 'b', 'c'] | '+'.join(self) }}  The result is 'a+b+c'
    
    If the expression is only one method invoker and the parameter is the 'self', we can 
    ignore the '(self)'.
    4) {{ 'abc' | parse(self) }} is same to {{ 'abc' | parse }}
    ```
    
  - property getter
    
    ```
    For the dictionary, we can get its value by the property getter:
    dic.keyname     - it can get the value from the dic with its key 'keyname'
 
    ```
    
  - blank trim
    
    ```
    1) If the expression starts with '{{-', it means trim the left blank including
       ' ', '\t', '\r', '\n'.
    2) If the expression ends with '-}}', it means trim the right blank including 
       ' ', '\t', '\r', '\n'.
    3) For the code block, it alwasy ignore the leading or trailing blank including 
       ' ', '\t', '\r', '\n'.
    ```
  


### 5. Extension
We can extend the template by writing a few python files with some global function in them. We use **@extension** To use it as follows:

```
{% @extension(py_file) %} 
```
#### Sample:
pytuils.py
```
def convert(i):
  return i*i
```

test.pt
```
{% @extension('pytuils.py') %} 
{% for i in range(1,6) %}
--{{i}}---{{i|convert}}--
{%endfor%}
```
Execute the command **python pt test.pt** to get the following result:
```
--1---1--
--2---4--
--3---9--
--4---16--
--5---25--
```

### 6. Include
A sub-template can be used in the current template by command **@include**, the offset of the sentence **{% @include(xx,xx) %}** will affect the output of the sub-template.

#### Sample:

student.pt
```
This is the first line. Print the input parameters as follows:
    a. Name : {{ student.name }}
    b. Score: {{ student.score }}
End.

``` 
students.pt
```
All students as follows:
==No index==
{% for student in students %}
{% @include('student.pt', {'student': student}) %}
{% endfor %}

==With index==
{% for idx, student in enumerate(students) %}
== {{ idx }} ==
    {% @include('student.pt', {'student': student}) %}
{% endfor %}
``` 
Execute the command **python pt students.pt -args "{'students': [{'name': 'joe', 'score': 88}, {'name': 'martin', 'score': 90}]}"** to get the following result:
```
All students as follows:
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

```

### 7. Output to File
One template can output to multiple files with command **@output_file**

#### Sample:
multiple_output.pt
```
{% @output_file('index.html') %}
<!DOCTYPE html>
<html>
    <head>
        <title>Index</title>
    </head>
    <body>
        <ul>
          {% for i in range(1, 11) %}
          <li><a href=".\pages\page{{i}}.html">Page {{i}}</a></li>
          {% endfor %}
        </ul>
    </body>
</html>
{% for i in range(1, 11) %}
{% @output_file('./pages/page' + str(i) + '.html') %}
<!DOCTYPE html>
<html>
    <head>
        <title>Page {{i}}</title>
    </head>
    <body>
        <p>This is page {{i}}.</p>
    </body>
</html>
{% endfor %}
```
Execute the command **python pt multiple_files.pt** to generated the following files:
```
index.html
pages\page1.html
pages\page2.html  
pages\page3.html  
pages\page4.html  
pages\page5.html  
pages\page6.html  
pages\page7.html  
pages\page8.html  
pages\page9.html  
pages\page10.html    
```

### 8. Add indent/Remove indent
The template can add/remove indent for the output text with command **@indent+**, **@indent-**

#### Sample:
indent_output.pt
```
{% if input['hasIf'] %}
if condition {
{% @indent+ %}
{% endif %}
fmt.println("test")
{% if input['hasIf'] %}
{% @indent- %}
}
{% endif %}  
fmt.println("test")
```
Execute the command **python pt indent_output.pt -args "{'input': {'hasIf': True}}"** to get the following result:
```
if condition {
  fmt.println("test")
}
fmt.println("test")
```
Execute the command **python pt indent_output.pt -args "{'input': {'hasIf': False}}"** to get the following result:
```
fmt.println("test")
fmt.println("test")  
```

### 9. Data Source
The template always has the data source to generate result. There are following ways to specify the data source for the template

#### 9.1 -args \<python dictionary>


#### 9.2 -ini  <argname=ini file>


#### 9.3 -json <argname=json file>


#### 9.4 -xml  <argname=xml file>


#### 9.5 -yaml <argname=yaml file>

### 10. LICENSE
Apache-2.0 License
