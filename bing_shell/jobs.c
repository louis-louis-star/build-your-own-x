/**
 * jobs.c - 后台任务管理模块
 * 
 * 功能：管理后台运行的任务
 */

#include "shell.h"

#define MAX_JOBS 100

/* 后台任务结构 */
typedef struct {
    pid_t pid;
    char command[256];
    int active;
} Job;

static Job jobs[MAX_JOBS];
static int job_count = 0;

/**
 * 添加后台任务
 */
void shell_add_job(pid_t pid, const char *cmd) {
    if (job_count < MAX_JOBS) {
        jobs[job_count].pid = pid;
        strncpy(jobs[job_count].command, cmd, sizeof(jobs[job_count].command) - 1);
        jobs[job_count].active = 1;
        job_count++;
    }
}

/**
 * 移除后台任务
 */
void shell_remove_job(pid_t pid) {
    int i;
    for (i = 0; i < job_count; i++) {
        if (jobs[i].pid == pid && jobs[i].active) {
            jobs[i].active = 0;
            printf("[%d]  Done                    %s\n", i + 1, jobs[i].command);
            break;
        }
    }
}

/**
 * 更新后台任务状态（检查已完成的任务）
 */
void shell_update_jobs(void) {
    int i;
    int status;
    
    for (i = 0; i < job_count; i++) {
        if (jobs[i].active) {
            pid_t result = waitpid(jobs[i].pid, &status, WNOHANG);
            if (result > 0) {
                jobs[i].active = 0;
                printf("[%d]  Done                    %s\n", i + 1, jobs[i].command);
            }
        }
    }
}

/**
 * 内置命令：jobs - 显示后台任务列表
 */
int shell_jobs(char **args) {
    int i;
    (void)args;
    
    /* 先更新任务状态 */
    shell_update_jobs();
    
    int count = 0;
    for (i = 0; i < job_count; i++) {
        if (jobs[i].active) {
            count++;
            printf("[%d]  Running                 %s\n", i + 1, jobs[i].command);
        }
    }
    
    if (count == 0) {
        printf("No background jobs.\n");
    }
    
    return 1;
}

