"""
将RPA生成的流程文件编译为Python代码
"""
import json
import os


class CodeBuilder:
    """
    用于增加代码行、管理缩进，最终给我们编译好的Python代码
    一个CodeBuilder对象对一整块Python代码负责

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

    def save_file(self, file_path):
        """
        保存代码文件
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(self))


class FlowCodeBuilder:
    """
    将RPA生成的流程文件编译为Python代码文件
    生成的Python文件保存在同文件夹中
    命名为当前json文件名去掉.flow
    """

    def __init__(self, flow_path):
        with open(flow_path, 'r', encoding='utf-8') as f:
            self.info = json.load(f)

        code = CodeBuilder()
        module_import = code.add_section()  # 用于生成导入语句
        code.add_line("def main():")
        code.indent()

        # 用于处理嵌套结构的栈
        ops_stack = []

        # 依次处理每个组件并生成代码
        blocks = self.info.get("blocks", [])
        for block_index, block in enumerate(blocks, start=1):
            self.generate_block_code(block, code, module_import, ops_stack, block_index)

        # 控制导入语句与函数之间的空行
        if len(module_import.code) > 1 and module_import.code[-2] != '\n':
            module_import.add_line("")

        # 判断是否空函数
        if len(code.code) == 4:
            code.add_line("pass")

        # 保存代码文件
        file_path = os.path.split(flow_path)[0]
        file_name = os.path.split(flow_path)[-1].split('.')[0] + '.py'
        code.save_file(os.path.join(file_path, file_name))

    def generate_block_code(self, block, code, module_import, ops_stack, block_index):
        """
        根据单个组件信息生成相应代码
        """
        # 获取组件名称
        block_name = block.get('name')

        # 判断是否启用组件
        isEnabled = block.get('isEnabled')
        if not isEnabled:
            code.add_line("# {}".format(block_name))
            return

        # 生成错误处理语句
        handle = block.get('exception_handling')
        if handle is not None:
            mode, retryTime, retryInterval = handle.get('mode'), handle.get(
                'retryTime'), handle.get('retryInterval')
            if mode == "retry":
                code = self.generate_handler_retry_code(code, module_import, retryTime, retryInterval)
            elif mode == "continue":
                code = self.generate_handler_continue_code(code)
        else:
            pass
        
        inputs, outputs = block.get('inputs'), block.get('outputs')
        # 根据组件类型生成相应代码
        func = getattr(self, "generate_"+block_name.split('.')[-1]+"_code")
        func(code, module_import, ops_stack, block_index, inputs, outputs)

    def generate_if_code(self, code, module_import, ops_stack, block_index, inputs, outputs):
        code.add_line("if xbot_visual.workflow.test(operand1=\"{}\", operator=\"{}\", operand2=\"{}\", _block=(\"main\", {})):".format(
            inputs["operand1"]["value"].split(":")[-1],
            inputs["operator"]["value"].split(":")[-1],
            inputs["operand2"]["value"].split(":")[-1],
            block_index
        ))
        code.indent()
        ops_stack.append('if')

    def generate_endif_code(self, code, module_import, ops_stack, block_index, *args):
        pass

    def generate_handler_retry_code(self, code, module_import, retryTime, retryInterval):
        code.add_line("for retry_time in range({}):".format(retryTime))
        code.indent()
        code.add_line("try:")
        code.indent()
        component_code = code.add_section()
        code.add_line("break")
        code.dedent()
        code.add_line("except Exception as e:")
        code.indent()
        code.add_line("if retry_time == 0:")
        code.indent()
        code.add_line("raise e")
        code.dedent()
        code.add_line("else:")
        code.indent()
        code.add_line("pass")
        code.dedent()
        code.dedent()
        code.add_line("time.sleep({})".format(retryInterval))
        code.dedent()
        module_import.add_line("import time")
        return component_code

    def generate_handler_continue_code(self, code):
        code.add_line("try:")
        code.indent()
        component_code = code.add_section()
        code.dedent()
        code.add_line("except Exception as e:")
        code.indent()
        code.add_line("pass")
        code.dedent()
        return component_code

if __name__ == "__main__":
    FlowCodeBuilder(r'C:\Users\lenovo\Desktop\main.flow.json')