# 模板引擎
> 项目来自[500 lines or less](http://aosabook.org/en/500L/a-template-engine.html)系列中的A Template Engine

## 简介
大部分程序都有很多逻辑处理，只有少量文本数据，编程语言就是为这类编程任务设计的。然而某些编程任务中，逻辑很少但是文本内容很多。对于这些任务，我们希望有一个更好的工具来解决这些文字为主的问题。

Web应用程序是以文字为主的任务的最常见例子。任何Web应用程序的一个重要阶段就是生成HTML送达至浏览器。只有很少的HTML页面是纯静态的，它们基本上至少含有一小点动态数据，例如用户名。通常它们含有更多的动态数据：产品列表，朋友的新消息等等。

同时，每个HTML页面含有大片静态文本。并且这些页面都很庞大，包含文本的字节数以万计。那么，Web应用程序开发者面临一个问题：怎样生成一个静态和动态数据混合的大型字符串是最好的？此外，静态文本内容实际上是HTML标记语言，这种生成方式最好是前端设计师熟悉的。

为了说明，我们假设要生成这种极简的HTML片段：
```
<p>Welcome, Charlie!</p>
<p>Products:</p>
<ul>
  <li>Apple: $1.00</li>
  <li>Fig: $1.50</li>
  <li>Pomegranate: $3.25</li>
</ul>
```
在这里，用户名将是动态的，产品的名称和价格也将是动态的，甚至产品种类的数量也是不固定的，因为库存是变动的。

## 模板
生成HTML的一种方式是在我们的代码中加入模板字符串，再将它们和动态数据结合在一起来产生页面。动态数据将以某种字符串格式化的形式插入。诸如python的`"foo = {foo}!".format(foo=17)`这样的字符串格式化函数是一个典型例子，这种用法是根据字符串字面量和要被插入的数据创建文本。模板运用了这个想法，不过程度更深。之所以被称为模板，是因为它们被用来产生许多具有相似结构与不同细节的页面。我们的某些动态数据的展现形式是重复的，比如我们的产品列表，这意味着我们有一批重复的HTML片段，所以我们将它单独处理再与其它部分组合。
以上述方式生成页面，得到的python代码将是这样的：
```
# The main HTML for the whole page.
PAGE_HTML = """
<p>Welcome, {name}!</p>
<p>Products:</p>
<ul>
{products}
</ul>
"""

# The HTML for each product displayed.
PRODUCT_HTML = "<li>{prodname}: {price}</li>\n"

def make_page(username, products, format_price=lambda price:'$'+price):
    product_html = ""
    for prodname, price in products:
        product_html += PRODUCT_HTML.format(
            prodname=prodname, price=format_price(price))
    html = PAGE_HTML.format(name=username, products=product_html)
    return html
```
它能工作，但是给我们增加了很多麻烦。HTML片段拆分在多个模板字符串里，嵌入在应用代码中。页面的逻辑很不清晰，因为静态内容被分成了几片。数据如何被格式化的细节丢失在python代码中。为了修改HTML页面，我们必须修改python代码。倘若页面非常复杂，这种方式就让人手足无措了。

## 扩展模板
上面的形式最主要的缺陷在于模板字符串中能够提供的信息太少，为了让我们的模板提供更多的信息，我们需要为其引入更多语法规则。

不同的模板支持的语法不同，我们的模板语法基于Django，一个流行的Web框架。下面是我们将实现的扩展后的语法规则：

1. 上下文中的数据使用双大括号插入
   
   `<p>Welcome, {{user_name}}!</p>`
   
2. 圆点将访问对象的属性或者字典的值，并且如果结果值是可调用的，它将被自动调用

   `<p>The price is: {{product.price}}, with a {{product.discount}}% discount.</p>`

3. 可以使用被称作过滤器的函数来修改值。过滤器通过一个竖线（管道符）来调用

   `<p>Short name: {{story.subject|slugify|lower}}</p>`

4. 支持条件语句

   ```
   {% if user.is_logged_in %}
       <p>Welcome, {{ user.name }}!</p>
   {% endif %}
   ```

5. 支持for循环

   ```
   <p>Products:</p>
   <ul>
   {% for product in product_list %}
       <li>{{ product.name }}: {{ product.price|format_price }}</li>
   {% endfor %}
   </ul>
   ```

6. 支持注释，注释出现在大括号和井号之间

   `{# This is the best template ever! #}`


另外，我们还需要与模板等价的python代码：一个接收参数为一个静态模板（包含结构和页面的静态内容）和一个动态上下文（提供嵌入模板的动态数据）的函数。这个函数结合了模板和上下文来生成一个纯HTML的字符串。它主要的任务是翻译模板，用动态数据替换其中的动态片段。

扩展后的模板是这样的：
```
<p>Welcome, {{user_name}}!</p>
<p>Products:</p>
<ul>
{% for product in product_list %}
    <li>{{ product.name }}:
        {{ product.price|format_price }}</li>
{% endfor %}
</ul>
```
有了上面的模板，我们就可以编写与之对应的python代码：
```
def render_function(context, do_dots):
    c_user_name = context['user_name']
    c_product_list = context['product_list']
    c_format_price = context['format_price']

    result = []
    append_result = result.append
    extend_result = result.extend
    to_str = str

    extend_result([
        '<p>Welcome, ',
        to_str(c_user_name),
        '!</p>\n<p>Products:</p>\n<ul>\n'
    ])
    for c_product in c_product_list:
        extend_result([
            '\n    <li>',
            to_str(do_dots(c_product, 'name')),
            ':\n        ',
            to_str(c_format_price(do_dots(c_product, 'price'))),
            '</li>\n'
        ])
    append_result('\n</ul>\n')
    return ''.join(result)
```
这个函数接受一个叫做context的数据字典。函数体先解析上下文字典中的数据到本地变量，因为对于数据的重复使用这样会快些。所有的上下文数据以加上c_前缀的形式变为本地变量，这样我们可以自由使用本地变量名而不用担心命名冲突。

函数运行的结果是一个字符串。
从一些组成部分构建一个字符串的最快方式就是创建一个字符串列表，然后用join组合在一起。
result就是一个字符串列表。
因为需要添加字符串到这个列表中，所以将它的append和extend方法赋给本地变量。
最后一个本地变量是一个内置方法str的速记——to_str。

字符串方法赋给本地变量是一种微型优化，可以节省我们少量时间。
因为避免了再花时间去查找对象的append和extend方法，
而是保存在变量中直接调用。

str的快捷方式同样是一个微优化。
在python中变量可以是函数本地的或者模块全局的或者是python内置的，
查找一个本地变量名的速度要比查找一个全局或内置的名称快。
我们习惯于str是一个总是可获得的内置函数，但是python仍然不得不在每次使用它时查找变量名，
将它放在一个本地变量中又为我们节省了一小块的时间，因为本地的要比内建的快。

下面考虑从我们的特定模板中生成的python代码，
字符串将被使用append_result或者extend_result快捷键添加到result列表，
选择前一个还是后一个取决于我们只有一个字符串要添加还是多个。

同时具有append和extend方法增加了复杂性，但请记住我们的目的是模板的最快执行。
对一个项目使用extend意味着要创建该项目的新列表这样我们才能将它传递给extend，
因此只有一个字符串的时候可以尽量使用append。

在`{{...}}`中的表达式将被计算，转换为字符串，并被添加到result。
表达式中的点将被传入渲染函数的do_dots函数处理，
因为加点的表达式的意义取决于context中的数据形式：它可能是属性访问、子项目获取或者是一个调用。

`{% if ... %}`和`{% for ... %}`的逻辑结构都转换为python的条件语句和循环。
在`{% if/for ... %}`标签中的表达式将会变成if/for语句中的表达式，
然后直到`{% end... %}`标签之前的内容都会变成语句的主体。


## 模板引擎
每个模板都有一个render_function函数与之对应，手动为模板编写函数是不现实的。因此我们引入模板引擎的概念，这个模板引擎要么能够先将模板转化为等价的函数，然后提供参数并执行这个函数来得到最后的HTML片段；要么直接读取模板内容和参数信息，然后根据与模板规则对应的处理方式依次将模板的各个部分转化成HTML片段。两种形式分别称为*编译*和*解释*，使用了和其他语言实现相关的术语。

这两种形式都涉及两个阶段：解析模板，然后渲染模板。

在一个解释模型中，解析产生一个数据结构表示模板的结构。渲染阶段遍历那个数据结构，基于找到的指令装配结果文本。一个真实的例子是Django模板引擎使用这种方法。

在一个编译模型中，解析产生某种形式的可直接执行的代码。渲染阶段执行那个代码，产生结果。Jinja2和Mako都是使用编译方法的模板引擎。

我们实现的模板引擎使用编译方法：我们将模板编译为python代码。执行时，代码将结果组装起来。总体而言，如果模板被编译为python代码，程序运行速度更快，因为即使编译过程比较复杂，它也只需要运行一次，而被编译的代码执行了很多次，要比解释一个数据结构很多次快很多。

将模板编译为python代码有点复杂，但是没有你想的那么糟糕。此外，编写能够写代码的程序比编写程序本身有趣多了！我们的模板编译器是一个代码生成的通用技术的小例子。代码生成技术构成许多强大而灵活的工具的基础，包括编程语言编译器。代码生成可以变得很复杂，但它是一个很值得拥有的有用的技术。

如果模板每次只会被使用很少次，这样的模板应用可能倾向于解释方法。编译模板为python代码的代价从长远看有些大了，整体看来，一个更简单的解释过程可能会更好。