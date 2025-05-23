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

```

### 3. Code Block
The code block is starts with '{%' and ends of '%}'. There are two kinds of code block.

#### 3.1 Built-in Code
The Built-in code must appear in the single line, the left and right blanks are ignored.

```
{% for var in var-list %}
# in the loop, the built-in variable 'var_idx'(0-based) can be used in the template
{% endfor %}

{% for key,val in var-dict.items() %}
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
Execute the command **python pt multiple_files.pt** to generate the following files:
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
- We can use **-args** and following a Python dictionary to specify the input data.
##### Sample:
test_args.pt
```
{% if input['hasIf'] %}
if condition {
{% endif %}
  fmt.println("test")
{% if input['hasIf'] %}
}
{% endif %}  
```
Execute the command **python pt test_args.pt -args "{'input': {'hasIf': True}}"** to get the following result:
```
if condition {
  fmt.println("test")
}
```
#### 9.2 -ini  <argname=ini file>
- We can use **-ini** and following a INI file to specify the input data.
##### Sample:
test_ini.pt
```
{{x.a}}
{{x.b}}
{{x.c}}
{{x.sec2.e}}
{{x.sec2.f}}
```
file.ini
```
  a = 123
  b = ab
  c = ['a','b']
  [sec2]
  e = 34
  f = ff
```
Execute the command **python pt test_ini.pt -ini x=file.ini** to get the following result:
```
123
ab
['a','b']
34
ff
```

#### 9.3 -json <argname=json file>
We can use **-json** and following a JSON file to specify the input data.
- **JSON object**: We store JSON object as a OrderedDict.
- **JSON array**:  We store JSON array as an array.
##### Sample:
test_json.pt
```
{{x.num}}
{{x.bool}}
{{x.array[0]}}
{{x.array[1]}}
{{x.array[2]}}
{{x.dic.key1}}
{{x.dic.key2}}
```
file.json
```
{
    "num"  : 1234,
    "bool" : true,
    "array": ["str", 123, true],
    "dic"  : {
                "key1": "val1",
                "key2": "val2"
             }
}
```
Execute the command **python pt test_json.pt -json x=file.json** to get the following result:
```
1234
true
str
123
true
val1
val2
```

#### 9.4 -xml  <argname=xml file>
We can use **-xml** and following a XML file to specify the input data.
##### For every XML node, it expose the following properties:
- **tag**: XML tag.
- **attrs**: The attributes of the XML element, it is a OrderedDict.
- **text**: The text of the XML element.
- **childs**:The children of the XML element, it is an array (0-based index).
- **{child_name}**: Specify a single child node
- **{child_name}[n]**: Specifies a child node that appears multiple times (0-based index).
##### Sample:
test_xml.pt
```
{{x.tag}}
{{x.attrs.attr1}}
{{x.attrs.attr2}}
{{x.attrs.attr3}}

{{x.node[0].attrs.n}}
{{x.node[1].text}}
{{x.single.attrs.a}}
{{x.single.text}}

{{x.childs[1].text}}
{{x.childs[2].text}}
```
file.xml
```
<joe attr1="abc" attr2="3" attr4="true">
    <node n="node.n" m="node.m">i'm the first node</node>
    <node>
        i'm the second node
    </node>
    <single a="single.a">single text</single>
</joe>
```
Execute the command **python pt test_xml.pt -xml x=file.xml** to get the following result:
```
joe
abc
3
true

node.n
i'm the second node
single.a
single text

i'm the second node
single text
```

#### 9.5 -yaml <argname=yaml file>
We can use **-yaml** and following a YAML file to specify the input data.
##### For every XML node, it expose the following properties:
- **tag**: XML tag.
- **attrs**: The attributes of the XML element, it is a OrderedDict.
- **text**: The text of the XML element.
- **childs**:The children of the XML element, it is an array.
- **child_name**: Specify a single child node
- **child_name[n]**: Specifies a child node that appears multiple times (0-based index).
##### Sample:
test_yaml.pt
```
{{x.openapi}}
{{x.info.title}}

{{x.info.description}}

{{x.paths./path/path1/path2.post.responses.'200'.content.application/json.schema.$ref}}
{{x.components.schemas.Data_Struct.properties.serverStatus.enum[0]}}
```
file.yaml
```
openapi: 3.0.0
info:
  title: Test
  version: '1.0'
  description: 'desc'
paths:
  /path/path1/path2:
    post:
      summary: 'DoSomething'
      description: 'DoSomething description.'
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Data_Struct'
        '400':
          summary: '400 summary'
components:
  schemas:
    Data_Struct:
      type: object
      properties:
        serverStatus:
          type: integer
          description: "desc"
          enum:
            - 0 - ONE
            - 1 - TWO
        str:
          type: string
          description: "desc"
        sessions:
          type: array
          items:
            type: string
```
Execute the command **python pt test_yaml.pt -yaml x=file.yaml** to get the following result:
```
3.0.0
Test

'desc'

'#/components/schemas/Data_Struct'
'0 - ONE'
```
#### 9.6 -kv <argname=Key-Value file>
We can use **-kv** and following a Key-Value file to specify the input data.
- We will parse the file line by line, if the line contains '=', we will split it to 2 parts, the first part is key, and the second part is the value.
- We will skip invalid key-value line.
##### Sample:
test_kv.pt
```
{{x.a}}
{{x.b}}
{{x.c}}
```
file.txt
```
    This is a test file
    
    other
    
    a = 123
    b = ab
    c = ['a','b']
    
    test test test
```
Execute the command **python pt test_kv.pt -kv x=file.txt** to get the following result:
```
123
ab
['a','b']
```

#### 9.7 -sql <argname=SQLite file,query>
We can use **-sql** and following a SQLite file, query statement to specify the input data.
- **query**  - SQLite query statement.
- **result** - If no rows are found, returns None; If only one row is found, returns the row as an OrderedDict; otherwise, returns all rows as a list of OrderedDict objects.
##### Sample:
 **python pt test_sql.pt -sql "x=file.db,SELECT * FROM product"** to get the result.

### 10. LICENSE
Apache-2.0 License
