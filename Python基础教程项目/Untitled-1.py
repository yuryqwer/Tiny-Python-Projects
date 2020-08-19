def mro(cls):
    # 获取直接基类
    bases = cls.__bases__
    # 只有一个父类，最常见所以放在第一个
    if len(bases) == 1:
        return [cls] + mro(bases[0])
    # object类
    elif len(bases) == 0:
        return [cls]
    # 同时继承多个父类
    else:
        return [cls] + merge(*[mro(C) for C in bases], list(bases))

def merge(*li):
    """
    遍历执行merge操作的序列
    如果一个序列的第一个元素，是其他序列中的第一个元素，或不在其他序列出现，则从所有执行merge操作序列中删除这个元素，合并到当前的mro中
    merge操作后的序列，继续执行merge操作，直到merge操作的序列为空
    """
    # merge的每个元素都为空
    if any(li) is False:
        return []
    else:
        res = []
        non_empty = list(filter(None, li))
        for seq in non_empty:
            candidate = seq[0]
            not_head = [s for s in non_empty if candidate in s[1:]]
            if not_head:
                candidate = None
            else:
                break
        if not candidate:
            raise TypeError("inconsistent hierarchy, no C3 MRO is possible")
        res.append(candidate)
        for seq in non_empty:
            if seq[0] == candidate:
                del seq[0]
        return res + merge(*non_empty)

######################################################################
def mro_C3(*cls):
    if len(cls) == 1:
        # object类
        if not cls[0].__bases__:
            return cls
        # 该类有基类
        else:
            return cls + mro_C3(*cls[0].__bases__)
    else:
        seqs = [list(mro_C3(C)) for C in cls] + [list(cls)]
        res = []
        while True:
            non_empty = list(filter(None, seqs))
            if not non_empty:
                return tuple(res)
            for seq in non_empty:
                candidate = seq[0]
                not_head = [s for s in non_empty if candidate in s[1:]]
                if not_head:
                    candidate = None
                else:
                    break
            if not candidate:
                raise TypeError("inconsistent hierarchy, no C3 MRO is possible")
            res.append(candidate)
            for seq in non_empty:
                if seq[0] == candidate:
                    del seq[0]
###########################################################################
"""
    O
 /  |  \
A1  A2  A3
| / | \ |
B1  B2  B3
| \ | \ |
C1  C2  C3
 \  |   /
    D
"""

class A1: pass
class A2: pass
class A3: pass
class B1(A1, A2): pass
class B2(A2): pass
class B3(A2, A3): pass
class C1(B1): pass
class C2(B2, B1): pass
class C3(B2, B3): pass
class D(C1, C2, C3): pass

print([cls.__name__ for cls in mro(D)])

# 规则表
RULES = [
    "A1 -> O",
    "A2 -> O",
    "A3 -> O",
    "B1 -> A1",
    "B1 -> A2",
    "A1 -> A2",
    "B2 -> A2",
    "B3 -> A2",
    "B3 -> A3",
    "A2 -> A3",
    "C1 -> B1",
    "C2 -> B2",
    "C2 -> B1",
    "B2 -> B1",
    "C3 -> B2",
    "C3 -> B3",
    "B2 -> B3",
    "D -> C1",
    "D -> C2",
    "D -> C3",
    "C1 -> C2",
    "C2 -> C3"
]

# 输出一个序列，能满足规则表
# 如果规则表有冲突，则抛出异常
['D', 'C1', 'C2', 'C3', 'B2', 'B1', 'A1', 'B3', 'A2', 'A3', 'O']


class Node:
    """
    有向图顶点类
    """
    def __init__(self, name):
        self.name = name
        self.in_nodes = set()
        self.out_nodes = set()

    def __repr__(self):
        return self.name

    def in_node(self, Node):
        """
        添加入度
        """
        self.in_nodes.add(Node)

    def out_node(self, Node):
        """
        添加出度
        """
        self.out_nodes.add(Node)

    def del_in_node(self, Node):
        try:
            self.in_nodes.remove(Node)
        except KeyError:
            pass

    def del_out_node(self, Node):
        try:
            self.out_nodes.remove(Node)
        except KeyError:
            pass

    def get_in(self):
        return len(self.in_nodes)

    def get_out(self):
        return len(self.out_nodes)

class Graph:
    """
    有向无环图
    """
    def __init__(self):
        self.nodes = []

    def add_rule(self, rule):
        """
        规定A > B 表示从A 指向 B
        """
        node1, direction, node2 = rule.split()
        assert direction in ['->', '<-'], '规则错误'
        Node1, Node2 = None, None
        for node in self.nodes:
            if node.name == node1:
                Node1 = node
            elif node.name == node2:
                Node2 = node
        if not Node1:
            Node1 = Node(node1)
            self.nodes.append(Node1)
        if not Node2:
            Node2 = Node(node2)
            self.nodes.append(Node2)
        if direction == '->':
            Node1.out_node(Node2)
            Node2.in_node(Node1)
        else:
            Node1.in_node(Node2)
            Node2.out_node(Node1)

g = Graph()

# 添加规则
for rule in RULES:
    g.add_rule(rule)

res = []

while g.nodes != []:
    for node in g.nodes:
        if node.get_in() == 0:
            break
    res.append(node)
    g.nodes.remove(node)
    for out_node in node.out_nodes:
        out_node.in_nodes.remove(node)

# 获取结果
print(res)