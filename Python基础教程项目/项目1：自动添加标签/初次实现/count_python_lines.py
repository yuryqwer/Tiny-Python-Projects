import os
import pprint

def count_lines(python_path):
    lines = 0
    with open(python_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            if line.strip() and not lines
        lines += 1
    return lines

def get_python_files(path, li=None):
    if not li:
        li = []
    for name in os.listdir(path):
        if os.path.isfile(os.path.join(path, name)) and name.endswith(".py"):
            lines = count_lines(os.path.join(path, name))
            if lines > 0:
                li.append((name, lines))
        elif os.path.isdir(os.path.join(path, name)):
            get_python_files(os.path.join(path, name), li)
    return li

def get_all_lines(li):
    return sum(_[1] for _ in li)


if __name__ == "__main__":     
    res = get_python_files(r'F:\RpaDesktopProgram\AutoWork\win-unpacked\resources\static\Python37-32\Lib\site-packages\RpaYzf')
    pprint.pprint(res)
    print(get_all_lines(res))