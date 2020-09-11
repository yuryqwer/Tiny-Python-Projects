def run_cmd_until_cond(path, cond, timeout=None):
    """
    运行命令行程序，当输出行满足cond条件时运行结束
    
    用子进程（这边的子进程不是python）运行程序并逐行判断输出
    如果输出满足某种条件则结束子进程
    注意bat文件如果有中文的话要用ANSI编码
    尽量设置超时时间，如果不设的话，当运行的bat中有pause
    且碰到pause时还没遇到符合条件的行就会一直卡死

    >>> run_cmd_until_cond(r'cd .. && dir', lambda text: False, 10)
    """
    import threading
    import subprocess
    proc = subprocess.Popen(path, shell=True,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    # 用子进程迭代处理行，方便控制超时时间
    def iter_row(iterator, cond):
        for line in iterator:
            try:  # 目前默认以utf-8解码，异常时用gbk解码
                linetext = line.decode("utf-8")
            except UnicodeDecodeError:
                linetext = line.decode("gbk")
            print(linetext, end="")
            if cond(linetext):
                return

    task = threading.Thread(target=iter_row, args=(
        iter(proc.stdout.readline, b''), cond))
    # task.setDaemon(True)  # 这边觉得还是不应该设置守护线程
    # 用停止proc的方法让子线程的for处理StopIteration异常并退出
    task.start()
    task.join(timeout=timeout)
    proc.terminate()
