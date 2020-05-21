"""
简易HTML模板引擎（https://www.jianshu.com/p/d6551dfacd58）

将HTML模板编译为Python代码，运行代码并提供相应的上下文，会生成HTML文本
"""
import re


class CodeBuilder:
    """
    用于增加代码行、管理缩进，最终给我们编译好的Python代码
    一个CodeBuilder对象对一整块Python代码负责
    对于我们的模板引擎，一整块Python代码始终是一个完整的函数定义
    但是CodeBuilder类并不会假设它只是一个函数，这让CodeBuilder更加通用
    并且与剩下的模板引擎代码的耦合度低

    另外，我们也使用嵌套的CodeBuilders来让代码可以放在函数前
    即使我们可能直到完成的时候才知道它到底做了什么

    一个CodeBuilder对象保存一个字符串列表，该列表将被组合成最终的Python代码
    它唯一需要的其他状态是当前的缩进级别
    """
    def __init__(self, indent=0):
        self.code = []
        self.indent_level = indent

    def add_line(self, line):
        """
        添加一行新代码，它会自动缩进到当前缩进级别，并在末尾提供一个换行符
        """
        self.code.extend([" " * self.indent_level, line, "\n"])

    INDENT_STEP = 4

    def indent(self):
        """
        增加当前的缩进级别
        """
        self.indent_level += self.INDENT_STEP

    def dedent(self):
        """
        降低当前的缩进级别
        """
        self.indent_level -= self.INDENT_STEP

    def add_section(self):
        """
        添加一个子CodeBuilder
        可以在代码中保留一个CodeBuilder对象，之后可以在那边添加代码
        self.code列表主要保存字符串，但是也可以保存对CodeBuilder片段的引用
        """
        section = CodeBuilder(self.indent_level)
        self.code.append(section)
        return section

    def __str__(self):
        """
        将self.code中的字符串拼接起来，在str(obj)的时候会被调用
        因为self.code中可以包含其他CodeBuilder对象，可能会递归调用那些对象的__str__方法
        """
        return "".join(str(c) for c in self.code)

    def get_globals(self):
        """
        执行包含python代码的字符串，并收集字符串代码中定义的全局变量，保存在字典中
        """
        # 检查CodeBuilder已经结束所有缩进
        assert self.indent_level == 0
        python_source = str(self)
        global_namespace = {}
        exec(python_source, global_namespace)
        return global_namespace

class TempliteSyntaxError(ValueError):
    """
    自定义异常类
    """
    pass

class Templite:
    """
    模板引擎的核心
    可以利用模板中的文本构建一个Templite对象
    然后可以使用它的render方法来渲染一个特定的上下文（数据字典）到模板中

    # Make a Templite object.
    templite = Templite('''
        <h1>Hello {{name|upper}}!</h1>
        {% for topic in topics %}
            <p>You are interested in {{topic}}.</p>
        {% endfor %}
        ''',
        {'upper': str.upper},
    )

    # Later, use it to render some data.
    text = templite.render({
        'name': "Ned",
        'topics': ['Python', 'Geometry', 'Juggling'],
    })

    我们将模板中的文本在对象创建时传递给它
    这样我们就能只做一次编译步骤，然后多次调用render函数来重用编译结果

    构造函数也接受一个字典来作为初始的上下文
    这些数据被存储在Templite对象里，并且之后当模板被渲染时可以获取
    这个位置适合于一些我们希望能随时获取的函数和常量，比如之前例子中的upper函数
    """
    def __init__(self, text, *contexts):
        """
        用给定的text模板构建一个Templite对象
        contexts是可以用于后续渲染的字典
        对于全局变量和过滤器来说很有用
        """
        self.context = {}
        for context in contexts:
            self.context.update(context)
        self.all_vars = set()  # 跟踪模板中定义的所有变量名
        self.loop_vars = set()  # 跟踪模板中定义的循环变量名

        code = CodeBuilder()
        code.add_line("def render_function(context, do_dots):")
        code.indent()
        vars_code = code.add_section()  # 后续将在该处写上变量提取的语句
        code.add_line("result = []")
        code.add_line("append_result = result.append")
        code.add_line("extend_result = result.extend")
        code.add_line("to_str = str")

        buffered = []
        def flush_output():
            """
            定义内部函数来帮助缓冲输出字符串
            缓冲列表保存还未被写入函数源代码的字符串
            当我们的模板编译运行时，我们将向buffered添加字符串
            然后当我们遇到控制流节点（如if语句，循环的开始或末端）时，将它们追加到函数源代码

            flus_output函数是一个闭包，它引用了buffered和code
            这简化了函数调用：不必告诉flush_output刷新哪个缓冲区或者刷新到哪，它隐式地知道这些

            如果只有只有一个字符串被缓冲，那么append_result将被调用
            如果多于一个，extend_result被使用
            然后缓冲队列被清空来缓冲下一批的字符串

            余下的编译代码将是添加语句到缓冲队列
            然后最终调用flush_output来将它们写入CodeBuilder
            """
            if len(buffered) == 1:
                code.add_line("append_result({})".format(buffered[0]))
            elif len(buffered) > 1:
                code.add_line("extend_result([{}])".format(", ".join(buffered)))
            del buffered[:]
        
        # 定义一个字符串栈，在解析控制流结构时用于检查是否合理嵌套
        # 例如当我们碰到一个{% if ... %}标签，我们将'if'压入堆栈
        # 当我们碰到一个{% endif %}标签时，我们再将之前的'if'弹出堆栈
        # 如果栈顶没有'if'则报告错误
        ops_stack = []

        # 将模板根据不同规则分割成一个列表
        # 前面的(?s)是正则表达式的模式修饰符，表示更改.的含义，使它与每一个字符匹配（包括换行符）
        # *?表示非贪婪模式
        # 例如，这是模板文本：
        # <p>Topics for {{name}}: {% for t in topics %}{{t}}, {% endfor %}</p>
        # 它将被分割成如下的片段：
        # [
        #     '<p>Topics for ',               # literal
        #     '{{name}}',                     # expression
        #     ': ',                           # literal
        #     '{% for t in topics %}',        # tag
        #     '',                             # literal (empty)
        #     '{{t}}',                        # expression
        #     ', ',                           # literal
        #     '{% endfor %}',                 # tag
        #     '</p>'                          # literal
        # ]
        # 一旦文本被分割成这样的标记，我们就可以循环依次处理它们
        # 根据类型来分割它们，我们就可以分别处理每个类型
        tokens = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text)

        # 编译代码是一个关于这些标记的循环
        # 每个标记都被检查，看它是四种情况中的哪一个
        for token in tokens:
            # 注释类型，直接忽略
            if token.startswith('{#'):
                continue
            # 表达式类型
            elif token.startswith('{{'):
                expr = self._expr_code(token[2:-2].strip())
                buffered.append("to_str({})".format(expr))
            # 控制结构
            elif token.startswith('{%'):
                flush_output()
                words = token[2:-2].strip().split()
                # 计算表达式的值来决定是否生成代码
                if words[0] == 'if':
                    if len(words) != 2:
                        self._syntax_error("不合法的if语句", token)
                    ops_stack.append('if')
                    code.add_line("if {}:".format(self._expr_code(words[1])))
                    code.indent()
                elif words[0] == 'for':
                    if len(words) != 4 or words[2] != 'in':
                        self._syntax_error("不合法的for语句", token)
                    ops_stack.append('for')
                    self._variable(words[1], self.loop_vars)  # 检查变量语法并将其加入循环变量集合
                    code.add_line("for c_{} in {}:".format(words[1], self._expr_code(words[3])))
                    code.indent()
                # 取消if或者for语句末尾的缩进
                elif words[0].startswith('end'):
                    if len(words) != 1:
                        self._syntax_error("不合法的end语句", token)
                    end_what = words[0][3:]
                    if len(ops_stack) == 0:
                        self._syntax_error("end语句过多", token)
                    start_what = ops_stack.pop()
                    if start_what != end_what:
                        self._syntax_error("end语句不匹配", end_what)
                    code.dedent()
                # 标签不是if、for或者end
                else:
                    self._syntax_error("不合法的标签", words[0])
            # 文字内容
            else:
                # 连续的正则标记会在最后的tokens中产生一个空字符串在它俩之间
                # 而添加一个空字符串到输出中是没有意义的
                if token:
                    # 使用内置的repr函数来产生一个python字符串字面量
                    # 否则在运行flush_output的时候会将token两侧的引号去掉
                    buffered.append(repr(token))
        
        # 完成模板中所有标记的循环后检查是否漏掉结束标签
        if ops_stack:
            self._syntax_error("存在未匹配的控制结构", ops_stack[-1])

        flush_output()

        # 在循环中定义的变量不需要提取
        # 每个名称都变成函数定义最初的一行代码
        for var_name in self.all_vars - self.loop_vars:
            vars_code.add_line("c_{} = context[{!r}]".format(var_name, var_name))

        # 添加返回语句
        code.add_line("return ''.join(result)")
        code.dedent()

        # 执行CodeBuilder对象生成的代码并得到函数本身
        # 因为我们的代码是一个函数定义（以def render_function(...)开始）
        # 所以执行这个代码会定义render_function，但是并不执行函数体
        # 得到的self._render_function就是一个可调用的python函数
        # 我们会在渲染阶段使用它
        self._render_function = code.get_globals()['render_function']

    def _expr_code(self, expr):
        """
        将模板中的表达式编译成python表达式
        模板表达式可能只是一个简单的名字：
        {{user_name}}
        也可能复杂到包含属性访问和过滤器：
        {{user.name.localized|upper|escape}}
        """
        if "|" in expr:
            pipes = expr.split("|")
            # 将第一部分递归地转化为python表达式
            code = self._expr_code(pipes[0])
            # 余下的每一个管道片段都是一个函数名
            for func in pipes[1:]:
                # 将每一个函数名加入all_vars中便于在函数开头提取
                self._variable(func, self.all_vars)
                code = "c_{}({})".format(func, code)
        elif "." in expr:
            dots = expr.split(".")
            code = self._expr_code(dots[0])
            args = ", ".join(repr(d) for d in dots[1:])
            code = "do_dots({}, {})".format(code, args)
        else:
            self._variable(expr, self.all_vars)
            code = "c_{}".format(expr)
        return code

    def _syntax_error(self, msg, thing):
        """
        用于抛出异常信息
        """
        raise TempliteSyntaxError("{}: {!r}".format(msg, thing))

    def _variable(self, name, vars_set):
        """
        用正则来验证变量名是否有效
        并把变量加入vars_set集合中
        """
        if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", name):
            self._syntax_error("变量名不合法", name)
        vars_set.add(name)

    #######################编译期和渲染期分割线#######################
    def render(self, context=None):
        """
        利用context上下文信息来渲染模板
        """
        # 复制最初初始化时提供的上下文
        # 为了让连续的多个渲染函数调用不会看到相互的数据
        render_context = dict(self.context)
        # 调用render时传递的数据可能会覆盖初始化时提供的数据
        # 但是一般不会发生
        # 因为传递给构造器的上下文包含的是全局定义的过滤器和常量
        # 而传给render的上下文包含的是那一次渲染的特定数据
        if context:
            render_context.update(context)
        return self._render_function(render_context, self._do_dots)

    def _do_dots(self, value, *dots):
        """
        运行时对.表达式进行求值
        在编译期间一个模板表达式如x.y.z被转换为do_dots(x, 'y', 'z')
        本函数循环每个点后的名称
        先尝试是否是一个属性，不是的话再看它是否是一个字典的键
        """
        for dot in dots:
            try:
                value = getattr(value, dot)
            except AttributeError:
                value = value[dot]
            if callable(value):
                value = value()
        return value

if __name__ == "__main__":
    templite = Templite('''<h1>Hello {{name|upper}}!</h1>
{% for topic in topics %}
    <p>You are interested in {{topic}}.</p>
{% endfor %}''',
        {'upper': str.upper},
    )

    text = templite.render({
        'name': "Ned",
        'topics': ['Python', 'Geometry', 'Juggling'],
    })
    print('-'*30)
    print(text)