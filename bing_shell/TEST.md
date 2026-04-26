# bing_shell 测试文档

## 测试环境

- 操作系统: Linux (Ubuntu/Debian 推荐)
- 编译器: GCC
- 依赖库: libreadline-dev

## 编译测试

```bash
cd bing_shell
make clean && make
```

预期结果: 编译成功，无错误警告，生成 `bing_shell` 可执行文件。

---

## 功能测试用例

### 1. 基本命令执行

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 1.1 | `ls` | 列出当前目录文件 |
| 1.2 | `ls -la` | 列出当前目录所有文件（包含隐藏文件） |
| 1.3 | `pwd` | 显示当前工作目录 |
| 1.4 | `echo Hello` | 输出: Hello |
| 1.5 | `echo "Hello World"` | 输出: Hello World (引号已去除) |
| 1.6 | `echo 'Single Quotes'` | 输出: Single Quotes (引号已去除) |

### 2. 内置命令测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 2.1 | `help` | 显示帮助信息 |
| 2.2 | `cd /tmp` | 切换到 /tmp 目录 |
| 2.3 | `cd` | 切换到用户主目录 |
| 2.4 | `cd ~` | 切换到用户主目录 |
| 2.5 | `history` | 显示命令历史记录 |
| 2.6 | `exit` | 退出 shell |

### 3. 管道测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 3.1 | `ls | wc -l` | 输出文件数量 |
| 3.2 | `ls -la | grep ".c"` | 输出所有 .c 文件 |
| 3.3 | `cat file.txt | sort` | 排序输出文件内容 |
| 3.4 | `ps aux | grep bash | head -5` | 多级管道正常工作 |

### 4. 重定向测试

| 测试编号 | 测试命令 | 鄂期结果 |
|---------|---------|---------|
| 4.1 | `echo "test" > test.txt` | 创建 test.txt 内容为 test |
| 4.2 | `echo "append" >> test.txt` | 追加内容到 test.txt |
| 4.3 | `cat < test.txt` | 读取并显示 test.txt 内容 |
| 4.4 | `ls > files.txt` | 将文件列表写入 files.txt |

### 5. 后台任务测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 5.1 | `sleep 5 &` | 输出: [1] PID |
| 5.2 | `jobs` | 显示后台任务列表 |
| 5.3 | `fg %1` | 将任务1调至前台 |
| 5.4 | `bg %1` | 在后台继续任务1 |

### 6. 信号处理测试 (Ctrl+Z)

| 测试编号 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| 6.1 | 执行 `sleep 100`，按 Ctrl+Z | 输出: [1] Stopped sleep 100 (只打印一次) |
| 6.2 | 执行 `jobs` | 显示: [1] Stopped sleep 100 |
| 6.3 | 执行 `bg %1` | 输出: [1] sleep 100 & |
| 6.4 | 执行 `fg %1` | 将任务调到前台继续运行 |

### 7. 信号处理测试 (Ctrl+C)

| 测试编号 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| 7.1 | 执行 `sleep 100`，按 Ctrl+C | 终止进程，显示新提示符 |
| 7.2 | 在空命令行按 Ctrl+C | 显示新行和提示符，不退出 |

### 8. 变量展开测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 8.1 | `export TEST=hello` | 设置环境变量 |
| 8.2 | `echo $TEST` | 输出: hello |
| 8.3 | `echo "Value: $TEST"` | 输出: Value: hello |
| 8.4 | `echo $?` | 输出上一命令退出状态 |
| 8.5 | `export VAR="hello world"` | 设置带空格的变量 |
| 8.6 | `echo ${VAR}` | 使用花括号引用变量 |

### 9. 通配符测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 9.1 | `ls *.c` | 列出所有 .c 文件 |
| 9.2 | `ls *.h` | 列出所有 .h 文件 |
| 9.3 | `cat file?.txt` | 匹配 file1.txt, file2.txt 等 |
| 9.4 | `ls [a-z]*.txt` | 匹配小写字母开头的 .txt 文件 |

### 10. 别名测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 10.1 | `ll` | 等同于 `ls -alF` |
| 10.2 | `la` | 等同于 `ls -A` |
| 10.3 | `l` | 等同于 `ls -CF` |

### 11. Tab 补全测试

| 测试编号 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| 11.1 | 输入 `c` 然后按 Tab | 补全为 `cd` |
| 11.2 | 输入 `ex` 然后按 Tab | 补全为 `exit` |
| 11.3 | 输入 `h` 然后按 Tab | 显示可能的补全选项 |

### 12. 历史记录测试

| 测试编号 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| 12.1 | 执行几个命令后按上箭头 | 显示上一条命令 |
| 12.2 | 继续按上箭头 | 继续向前浏览历史 |
| 12.3 | 按下箭头 | 向后浏览历史 |
| 12.4 | 执行 `history` | 显示所有历史命令 |

### 13. 引号处理测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 13.1 | `echo "Hello World"` | 输出: Hello World |
| 13.2 | `echo 'Hello World'` | 输出: Hello World |
| 13.3 | `echo "Test 123"` | 输出: Test 123 |
| 13.4 | `echo > "file with spaces.txt"` | 创建文件名带空格的文件 |

### 14. 错误处理测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 14.1 | `nonexistent_command` | 输出错误信息，不崩溃 |
| 14.2 | `cd /nonexistent/path` | 输出错误信息 |
| 14.3 | `cat < nonexistent.txt` | 输出错误信息 |
| 14.4 | `fg %999` | 输出: fg: job 999 not found |

### 15. 链式命令测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 15.1 | `echo a; echo b` | 输出 a 和 b |
| 15.2 | `true && echo success` | 输出: success |
| 15.3 | `false && echo "not printed"` | 无输出 |
| 15.4 | `false || echo fallback` | 输出: fallback |
| 15.5 | `true || echo "not printed"` | 无输出 |

### 16. 子 Shell 测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 16.1 | `(cd /tmp && pwd)` | 输出: /tmp |
| 16.2 | `export x=outer; (export x=inner; echo $x); echo $x` | 输出: inner 然后 outer |
| 16.3 | `pwd; (cd /tmp); pwd` | 两次输出相同目录（子 shell 不影响父进程） |
| 16.4 | `((echo nested))` | 输出: nested（嵌套子 shell） |

### 17. 多行命令测试

| 测试编号 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| 17.1 | 输入 `echo hello \` 然后回车，再输入 `world` | 输出: hello world |
| 17.2 | 输入多行带续行符的命令 | 正确拼接执行 |

### 18. 外部命令测试

| 测试编号 | 测试命令 | 预期结果 |
|---------|---------|---------|
| 18.1 | `chmod 755 file.txt` | 修改文件权限成功 |
| 18.2 | `find . -name "*.txt"` | 查找文件成功 |
| 18.3 | `grep "pattern" file.txt` | 搜索成功 |
| 18.4 | `sed 's/old/new/' file.txt` | 替换成功 |
| 18.5 | `awk '{print $1}' file.txt` | 处理成功 |
| 18.6 | `tar -cvf archive.tar files` | 打包成功 |

---

## 自动化测试脚本

将以下脚本保存为 `test_shell.sh` 并运行：

```bash
#!/bin/bash

echo "=== bing_shell 自动化测试 ==="

# 测试基本命令
echo "测试 1: 基本命令..."
./bing_shell -c "echo Hello" | grep -q "Hello" && echo "  [PASS] echo 命令" || echo "  [FAIL] echo 命令"

# 测试管道
echo "测试 2: 管道..."
./bing_shell -c "ls | wc -l" && echo "  [PASS] 管道" || echo "  [FAIL] 管道"

# 测试重定向
echo "测试 3: 重定向..."
./bing_shell -c "echo test > /tmp/test_bing.txt"
cat /tmp/test_bing.txt | grep -q "test" && echo "  [PASS] 输出重定向" || echo "  [FAIL] 输出重定向"
rm -f /tmp/test_bing.txt

# 测试变量展开
echo "测试 4: 变量展开..."
./bing_shell -c "export TEST=hello; echo \$TEST" | grep -q "hello" && echo "  [PASS] 变量展开" || echo "  [FAIL] 变量展开"

echo "=== 测试完成 ==="
```

---

## 回归测试清单

修复问题后需要重新测试的项目：

### 修复 "引号没有去掉" 问题后
- [ ] `echo "Hello World"` 输出正确
- [ ] `echo 'Single'` 输出正确
- [ ] 重定向文件名带引号正常工作

### 修复 "Ctrl+Z 打印两遍" 问题后
- [ ] Ctrl+Z 只打印一次停止信息
- [ ] `jobs` 命令正确显示停止的任务
- [ ] `fg` 和 `bg` 命令正常工作

---

## 测试结果记录

| 日期 | 测试人员 | 通过/失败 | 备注 |
|-----|---------|----------|------|
| | | | |

---

## 已知问题

1. 无

## 修复历史

| 日期 | 问题描述 | 修复方案 |
|-----|---------|---------|
| | 引号没有去除 | 在 parse.c 添加 strip_quotes 函数 |
| | Ctrl+Z 打印两遍 | 移除 execute.c 中重复的打印语句 |
| | export 返回值错误 | 修改 export 成功时返回 0 |
| | 变量拼接失败 | 修复 shell_launch_command 返回值问题 |

## 新增功能

| 版本 | 功能 | 描述 |
|-----|------|------|
| v1.1 | 多行命令 | 支持 `\` 续行符实现多行输入 |
| v1.1 | 子 Shell | 支持 `(cmd)` 语法创建子进程执行命令 |
| v1.0 | 基本功能 | 管道、重定向、后台任务、变量展开等 |

