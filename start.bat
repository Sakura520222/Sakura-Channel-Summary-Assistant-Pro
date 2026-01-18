@echo off
chcp 65001 >nul
title Sakura 频道总结助手

:loop
echo.
echo ========================================
echo 正在启动机器人...
echo ========================================
echo.

python main.py

set EXIT_CODE=%ERRORLEVEL%

if exist data\temp\restart_flag (
    echo.
    echo ========================================
    echo 检测到重启标志，将在 3 秒后自动重启...
    echo 按 Ctrl+C 取消重启
    echo ========================================
    echo.
    del data\temp\restart_flag 2>nul
    timeout /t 3 /nobreak
    goto loop
) else if %EXIT_CODE% EQU 0 (
    echo.
    echo ========================================
    echo 程序正常退出
    echo ========================================
    echo.
    pause
) else (
    echo.
    echo ========================================
    echo 程序异常退出（错误码: %EXIT_CODE%）
    echo 将在 3 秒后自动重启...
    echo 按 Ctrl+C 取消重启
    echo ========================================
    echo.
    timeout /t 3 /nobreak
    goto loop
)
