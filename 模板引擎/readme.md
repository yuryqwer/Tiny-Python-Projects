# 模板引擎
> 项目来自[500 lines or less](http://aosabook.org/en/500L/a-template-engine.html)系列中的A Template Engine,
> 译者为[treelake](https://www.jianshu.com/p/b5d4aa45e771)

## 简介
大部分程序都有很多逻辑处理，只有少量文本数据，编程语言就是为这类编程任务设计的。然而某些编程任务中，逻辑很少但是文本内容很多。对于这些任务，我们希望有一个更好的工具来解决这些文字为主的问题。

Web应用程序是以文字为主的任务的最常见例子。在任何Web应用程序的一个重要阶段就是生成HTML送达至浏览器。只有很少的HTML页面是纯静态的，它们基本上至少含有一小点动态数据，例如用户名。通常它们含有更多的动态数据：产品列表，朋友的新消息等等。

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

生成HTML的一种方式是在我们的代码中加入字符串常量，再将它们和动态数据结合在一起来产生页面。动态数据将以某种字符串格式化的形式插入。我们的某些动态数据的展现形式是重复的，比如我们的产品列表，这意味着我们有一批重复的HTML片段，所以我们将它单独处理再与其它部分组合。
以上述方式生成页面将是这样的：
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

def make_page(username, products):
    product_html = ""
    for prodname, price in products:
        product_html += PRODUCT_HTML.format(
            prodname=prodname, price=format_price(price))
    html = PAGE_HTML.format(name=username, products=product_html)
    return html
```