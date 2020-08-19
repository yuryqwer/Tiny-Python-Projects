# RPA流程文件设计
> 定义前端产生的json文件

## 字段说明
* name：在设计器中显示的流程名称
* blocks：各组件的信息（list of dict）
  * name：组件名称，用于确定将要生成的代码规则（str）
  * isEnabled：是否启用组件（bool）
  * comment：组件上显示的文本，用前后%符号将需要格式化的变量括起来，前端会去输入输出里面寻找用于格式化的变量值（str）
  * note：组件备注信息，鼠标悬浮至组件时显示（str）
  * inputs：输入参数（dict）
    * xxx：输入参数名称（str）
    * 参数属性（dict）
      * value：设置的属性值，用于传递给生成的代码（str）
        * 字符串模式：以【10:】开头，后面的值在传递时会扩在引号中
        * 表达式模式：以【13:】开头，后面的值在传递时不会扩在引号中
        * null：没有填写value
      * display：前端显示的属性值，看起来更直观（str）
  * outputs：输出参数（dict）
    * xxx：输出参数名称（str）
    * 参数属性（dict）
      * name：生成的代码左侧的值，传递时不会扩在引号中
      * type：输出参数类型，便于前端在后续组件中筛选默认变量
  * exception_handling：错误处理（dict）
    * mode：处理模式
      * 终止流程
      * 忽略异常
      * 重试
    * retryTime：重试次数
    * retryInterval：重试间隔

# 流程文件编译器
> 将前端产生的json文件转为python代码，在前端保存的时候运行