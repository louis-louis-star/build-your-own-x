# bing_shell Makefile
# 编译和链接配置

CC = gcc
CFLAGS = -Wall -Wextra -g
LDFLAGS = -lreadline -lhistory
TARGET = bing_shell

# 源文件
SRCS = main.c readline.c parse.c execute.c builtin.c prompt.c signal.c
OBJS = $(SRCS:.c=.o)

# 默认目标：编译所有文件并链接
all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# 编译.c文件为.o文件
%.o: %.c shell.h
	$(CC) $(CFLAGS) -c $<

# 清理编译产物
clean:
	rm -f $(OBJS) $(TARGET)

# 重新编译
rebuild: clean all

# 调试运行
run: all
	./$(TARGET)

.PHONY: all clean rebuild run

