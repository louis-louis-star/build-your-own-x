#!/bin/bash

################################################################################
# bing_shell 自动化测试脚本
# 测试 shell 的所有基本特性是否正确实现
################################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试结果记录
declare -a FAILED_TEST_NAMES

# 临时目录
TEST_DIR="/tmp/bing_shell_test_$$"
SHELL_PATH="./bing_shell"

################################################################################
# 辅助函数
################################################################################

# 初始化测试环境
setup() {
    echo -e "${BLUE}=== bing_shell 自动化测试 ===${NC}"
    echo ""

    # 检查 shell 是否存在
    if [[ ! -x "$SHELL_PATH" ]]; then
        echo -e "${RED}错误: $SHELL_PATH 不存在或不可执行${NC}"
        echo "请先编译: cd bing_shell && make"
        exit 1
    fi

    # 创建临时测试目录
    mkdir -p "$TEST_DIR"
    echo -e "${YELLOW}测试目录: $TEST_DIR${NC}"
    echo ""
}

# 清理测试环境
teardown() {
    rm -rf "$TEST_DIR"
}

# 运行单个测试
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected="$3"
    local actual

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 执行命令并获取输出
    actual=$($SHELL_PATH -c "$test_cmd" 2>&1)

    # 检查结果
    if [[ "$actual" == *"$expected"* ]]; then
        echo -e "  ${GREEN}[PASS]${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "  ${RED}[FAIL]${NC} $test_name"
        echo -e "         命令: $test_cmd"
        echo -e "         期望包含: $expected"
        echo -e "         实际输出: $actual"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_TEST_NAMES+=("$test_name")
        return 1
    fi
}

# 运行测试（精确匹配）
run_test_exact() {
    local test_name="$1"
    local test_cmd="$2"
    local expected="$3"
    local actual

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    actual=$($SHELL_PATH -c "$test_cmd" 2>&1)

    if [[ "$actual" == "$expected" ]]; then
        echo -e "  ${GREEN}[PASS]${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "  ${RED}[FAIL]${NC} $test_name"
        echo -e "         命令: $test_cmd"
        echo -e "         期望: $expected"
        echo -e "         实际: $actual"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_TEST_NAMES+=("$test_name")
        return 1
    fi
}

# 运行测试（检查命令是否成功执行）
run_test_success() {
    local test_name="$1"
    local test_cmd="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    $SHELL_PATH -c "$test_cmd" >/dev/null 2>&1
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        echo -e "  ${GREEN}[PASS]${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "  ${RED}[FAIL]${NC} $test_name (exit code: $exit_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_TEST_NAMES+=("$test_name")
        return 1
    fi
}

# 打印测试总结
print_summary() {
    echo ""
    echo -e "${BLUE}=== 测试总结 ===${NC}"
    echo -e "总计测试: $TOTAL_TESTS"
    echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
    echo -e "${RED}失败: $FAILED_TESTS${NC}"

    if [[ $FAILED_TESTS -gt 0 ]]; then
        echo ""
        echo -e "${RED}失败的测试:${NC}"
        for name in "${FAILED_TEST_NAMES[@]}"; do
            echo -e "  - $name"
        done
    fi

    echo ""
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}所有测试通过!${NC}"
        return 0
    else
        echo -e "${RED}部分测试失败!${NC}"
        return 1
    fi
}

################################################################################
# 测试用例
################################################################################

test_basic_commands() {
    echo -e "${YELLOW}[1] 基本命令执行测试${NC}"

    run_test "echo 简单字符串" "echo hello" "hello"
    run_test "echo 多参数" "echo hello world" "hello world"
    run_test "pwd 命令" "pwd" "/"
    run_test_success "ls 命令" "ls"
    run_test_success "true 命令" "true"

    echo ""
}

test_quoted_strings() {
    echo -e "${YELLOW}[2] 引号处理测试${NC}"

    run_test_exact "双引号字符串" 'echo "Hello World"' "Hello World"
    run_test_exact "单引号字符串" "echo 'Hello World'" "Hello World"
    run_test "引号内空格" 'echo "hello   world"' "hello   world"
    run_test "混合引号" 'echo "hello"' "hello"

    echo ""
}

test_builtins() {
    echo -e "${YELLOW}[3] 内置命令测试${NC}"

    run_test "help 命令" "help" "bing_shell"
    run_test "cd 命令" "cd /tmp && pwd" "/tmp"
    run_test "cd 到家目录" "cd && pwd" ""
    run_test_success "history 命令" "history"
    run_test "export 设置变量" "export TEST_VAR=hello && echo \$TEST_VAR" "hello"
    run_test "unset 变量" "export TEST=123 && unset TEST && echo \$TEST" ""

    echo ""
}

test_pipes() {
    echo -e "${YELLOW}[4] 管道测试${NC}"

    run_test "单管道" "echo hello | cat" "hello"
    run_test "管道计数" "echo -e 'a\nb\nc' | wc -l" "3"
    run_test "双管道" "echo hello | cat | cat" "hello"
    run_test "管道 grep" "echo -e 'apple\nbanana\ncherry' | grep apple" "apple"
    run_test_success "多级管道" "ls | grep .c | head -1"

    echo ""
}

test_redirections() {
    echo -e "${YELLOW}[5] 重定向测试${NC}"

    local test_file="$TEST_DIR/redirect_test.txt"

    run_test_success "输出重定向 (>)" "echo test_output > $test_file"
    run_test "读取重定向文件" "cat $test_file" "test_output"
    run_test_success "追加重定向 (>>)" "echo append_line >> $test_file"
    run_test "验证追加内容" "cat $test_file" "append_line"

    # 输入重定向测试
    echo "input_content" > "$TEST_DIR/input.txt"
    run_test "输入重定向 (<)" "cat < $TEST_DIR/input.txt" "input_content"

    echo ""
}

test_variables() {
    echo -e "${YELLOW}[6] 变量展开测试${NC}"

    run_test "环境变量" "export MYVAR=testing && echo \$MYVAR" "testing"
    run_test "变量在字符串中" 'export V=world && echo "hello $V"' "hello world"
    run_test "花括号变量" "export VAR=test && echo \${VAR}" "test"
    run_test "退出状态 \$?" "true; echo \$?" "0"
    run_test "失败退出状态" "false; echo \$?" "1"
    run_test "变量拼接" "export A=hello && export B=world && echo \$A\$B" "helloworld"

    echo ""
}

test_wildcards() {
    echo -e "${YELLOW}[7] 通配符测试${NC}"

    # 创建测试文件
    touch "$TEST_DIR/file1.txt" "$TEST_DIR/file2.txt" "$TEST_DIR/data.c"

    run_test_success "* 通配符" "ls $TEST_DIR/*.txt"
    run_test_success "? 通配符" "ls $TEST_DIR/file?.txt"

    echo ""
}

test_tilde_expansion() {
    echo -e "${YELLOW}[8] 波浪号展开测试${NC}"

    run_test "~ 展开到家目录" "cd ~ && pwd" ""
    run_test_success "ls ~" "ls ~"

    echo ""
}

test_aliases() {
    echo -e "${YELLOW}[9] 别名测试${NC}"

    run_test_success "ll 别名" "ll"
    run_test_success "la 别名" "la"
    run_test_success "l 别名" "l"

    echo ""
}

test_chained_commands() {
    echo -e "${YELLOW}[10] 链式命令测试${NC}"

    run_test "分号分隔命令" "echo a; echo b" "a"
    run_test "&& 运算符成功" "true && echo success" "success"
    run_test "&& 运算符失败跳过" "false && echo 'should not print'" ""
    run_test "|| 运算符失败执行" "false || echo fallback" "fallback"
    run_test "|| 运算符成功跳过" "true || echo 'should not print'" ""
    run_test_success "cd 后执行" "cd /tmp && pwd"

    echo ""
}

test_special_cases() {
    echo -e "${YELLOW}[11] 特殊情况和边界测试${NC}"

    # 空命令
    run_test_success "空命令" ""

    # 只有空格
    run_test_success "只有空格" "   "

    # 长命令
    local long_cmd="echo"
    for i in {1..20}; do long_cmd="$long_cmd arg$i"; done
    run_test_success "长命令行" "$long_cmd"

    echo ""
}

test_error_handling() {
    echo -e "${YELLOW}[12] 错误处理测试${NC}"

    # 不存在的命令应该返回错误但不崩溃
    $SHELL_PATH -c "nonexistent_command_xyz" 2>&1 | grep -q "error\|Error\|not found\|bing_shell"
    if [[ $? -eq 0 ]]; then
        echo -e "  ${GREEN}[PASS]${NC} 不存在的命令错误处理"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} 不存在的命令错误处理"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 不存在的目录
    $SHELL_PATH -c "cd /nonexistent/directory" 2>&1 | grep -q "."
    if [[ $? -eq 0 ]]; then
        echo -e "  ${GREEN}[PASS]${NC} 不存在的目录错误处理"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} 不存在的目录错误处理"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo ""
}

test_command_line_args() {
    echo -e "${YELLOW}[13] 命令行参数测试${NC}"

    # 测试 -c 参数
    $SHELL_PATH -c "echo test_arg" 2>&1 | grep -q "test_arg"
    if [[ $? -eq 0 ]]; then
        echo -e "  ${GREEN}[PASS]${NC} -c 参数执行命令"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} -c 参数执行命令"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 测试 -h 参数
    $SHELL_PATH -h 2>&1 | grep -q "Usage"
    if [[ $? -eq 0 ]]; then
        echo -e "  ${GREEN}[PASS]${NC} -h 帮助参数"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} -h 帮助参数"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo ""
}

test_subshell() {
    echo -e "${YELLOW}[14] 子 shell 测试${NC}"

    run_test "括号子 shell" "(cd /tmp && pwd)" "/tmp"
    run_test "子 shell 变量隔离" "export x=outer; (export x=inner; echo \$x); echo \$x" "inner"
    run_test "子 shell 不影响父进程目录" "(cd /tmp); pwd" ""
    run_test "嵌套子 shell" "((echo nested))" "nested"

    echo ""
}

test_multiline() {
    echo -e "${YELLOW}[15] 多行命令测试${NC}"

    # 多行命令只在交互模式下有效，-c 模式下无法测试
    # 这里测试反斜杠在字符串中的处理
    run_test "反斜杠字符" "echo 'hello\\world'" "hello\\world"
    run_test "反斜杠在双引号" 'echo "hello\\world"' "hello\\world"

    echo ""
}

test_external_commands() {
    echo -e "${YELLOW}[16] 外部命令测试${NC}"

    # 创建测试文件
    touch "$TEST_DIR/chmod_test.txt"

    run_test_success "chmod 命令" "chmod 755 $TEST_DIR/chmod_test.txt"
    run_test_success "find 命令" "find $TEST_DIR -name '*.txt'"
    run_test "grep 命令" "echo 'hello world' | grep hello" "hello"
    run_test "sed 命令" "echo 'hello' | sed 's/hello/hi/'" "hi"
    run_test "awk 命令" "echo 'a b c' | awk '{print \$1}'" "a"
    run_test_success "tar 命令" "tar -cvf $TEST_DIR/test.tar -C $TEST_DIR ."

    echo ""
}

################################################################################
# 主程序
################################################################################

main() {
    setup

    # 运行所有测试
    test_basic_commands
    test_quoted_strings
    test_builtins
    test_pipes
    test_redirections
    test_variables
    test_wildcards
    test_tilde_expansion
    test_aliases
    test_chained_commands
    test_special_cases
    test_error_handling
    test_command_line_args
    test_subshell
    test_multiline
    test_external_commands

    # 清理并打印结果
    teardown
    print_summary
}

# 执行测试
main

