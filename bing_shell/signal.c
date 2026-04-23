/**
 * signal.c - 信号处理模块
 * 
 * 功能：处理 Ctrl+C (SIGINT) 等信号
 *
 * Ctrl+C - 清空当前行，重新显示提示符
 * Ctrl+D - 在 readline 中返回 NULL，由主循环处理退出
 * Ctrl+\ - 忽略 SIGQUIT
 */

#include "shell.h"
#include <signal.h>
#include <readline/readline.h>

/* 信号处理函数 */
static void sigint_handler(int sig) {
    (void)sig;
    
    /* 换行并重新显示提示符 */
    write(STDOUT_FILENO, "\n", 1);
    rl_on_new_line();
    rl_replace_line("", 0);
    rl_redisplay();
}

/**
 * 初始化信号处理
 */
void shell_init_signals(void) {
    struct sigaction sa;
    
    /* 处理 Ctrl+C (SIGINT) */
    sa.sa_handler = sigint_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    sigaction(SIGINT, &sa, NULL);
    
    /* 忽略 Ctrl+\ (SIGQUIT) */
    signal(SIGQUIT, SIG_IGN);
    
    /* 忽略子进程退出信号，避免僵尸进程 */
    signal(SIGCHLD, SIG_IGN);
}

