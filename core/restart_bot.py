# Copyright 2026 Sakura-频道总结助手
# 
# 本项目采用 GNU General Public License v3.0 (GPLv3) 许可证
# 
# 您可以自由地：
# - 商业使用：将本软件用于商业目的
# - 修改：修改本软件以满足您的需求
# - 分发：分发本软件的副本
# - 专利使用：明确授予专利许可
# 
# 您必须遵守以下条件：
# - 开源修改：如果修改了代码，必须开源修改后的代码
# - 源代码分发：分发程序时必须同时提供源代码
# - 相同许可证：修改和分发必须使用相同的GPLv3许可证
# - 版权声明：保留原有的版权声明和许可证
# 
# 本项目源代码：https://github.com/Sakura520222/Sakura-Channel-Summary-Assistant-Pro
# 许可证全文：https://www.gnu.org/licenses/gpl-3.0.html

import subprocess
import time
import os
import sys

print("正在重启Sakura频道总结助手...")

# 1. 先停止当前进程（通过taskkill）
try:
    # 查找并停止所有python进程（除了当前进程）
    import psutil
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                pid = proc.info['pid']
                if pid != current_pid:
                    # 检查是否在运行我们的脚本
                    try:
                        cmdline = proc.cmdline()
                        if 'main.py' in ' '.join(cmdline):
                            print(f"停止进程 {pid}: {cmdline}")
                            proc.terminate()
                            proc.wait(timeout=5)
                    except:
                        pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
except ImportError:
    # 如果没有psutil，使用taskkill
    os.system('taskkill /F /IM python.exe')
    time.sleep(2)

# 2. 等待端口释放
time.sleep(3)

# 3. 启动新进程
print("启动新的机器人进程...")
subprocess.Popen([sys.executable, 'main.py'])
print("重启完成！")
