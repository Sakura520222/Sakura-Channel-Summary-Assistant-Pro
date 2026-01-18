# 🌸 Sakura-频道总结助手 v1.0.0

[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Telethon](https://img.shields.io/badge/Telethon-1.34+-blue.svg)](https://docs.telethon.dev/)
[![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue.svg)](https://www.docker.com/)

> **专业的Telegram频道智能管理解决方案** - 基于AI技术的自动化频道内容管理和报告生成系统，专为提升频道管理效率而设计。

---

## 📋 产品简介

Sakura-频道总结助手是一款专业的Telegram频道管理工具，通过AI技术自动化处理频道消息，生成高质量的内容总结、投票互动和数据分析报告。本产品旨在帮助频道管理员节省时间、提升内容质量、增强用户互动。

### 核心价值

- **⚡ 提升效率**：自动化处理频道消息，节省80%以上的人工整理时间
- **🤖 AI驱动**：采用先进的AI模型，智能提取核心内容和价值点
- **📊 数据洞察**：完整的数据统计和历史分析，为内容决策提供依据
- **🎯 用户互动**：自动生成投票和互动内容，提升频道活跃度
- **🔧 灵活配置**：支持多频道、多频率、多管理员的企业级配置
- **🛡️ 稳定可靠**：完善的错误处理和恢复机制，确保服务稳定运行

---

## ✨ 产品特性

### 🤖 AI智能总结
- **多模型支持**：兼容DeepSeek、OpenAI等多种AI模型
- **自定义提示词**：灵活调整总结风格和输出格式
- **智能提取**：自动识别核心要点、关键信息、重要趋势
- **多频道处理**：同时监控和总结多个频道内容

### ⏰ 多频率自动总结
- **每天模式**：固定时间每天自动总结
- **每周模式**：指定多天每周自动总结
- **频道级配置**：不同频道设置不同的总结时间和频率

### 📊 数据管理与洞察
- **历史记录**：自动保存所有总结到SQLite数据库
- **多维统计**：总结次数、消息数量、频道排行等统计信息
- **数据导出**：支持JSON、CSV、md等多种格式导出
- **智能分析**：时间分布、类型分析、活跃度趋势

### 🎯 互动功能
- **自动投票**：根据总结内容自动生成投票问题
- **投票配置**：支持频道模式和讨论组模式
- **重新生成**：管理员可重新生成不理想的投票
- **互动增强**：提升频道用户参与度和活跃度

### 🛠️ 企业级管理
- **多管理员**：支持多个管理员同时管理
- **权限控制**：完善的权限管理和命令访问控制
- **健康监控**：实时监控服务状态和健康检查
- **日志管理**：可配置的日志级别，方便问题排查
- **智能防护**：自动检测恶意行为，保护机器人免受骚扰

### 🔧 技术优势
- **Docker容器化**：一键部署，易于管理和扩展
- **智能消息分割**：保护Markdown格式，确保消息完整性
- **错误恢复**：智能重试机制和优雅关闭
- **线程安全**：支持多线程并发处理，提升性能

---

## 🚀 快速开始

### 环境要求

- **Python 3.13+** 或 **Docker 20.10+**
- **Telegram Bot Token**（从 [@BotFather](https://t.me/BotFather) 获取）
- **Telegram API ID 和 API Hash**（从 [my.telegram.org](https://my.telegram.org) 获取）
- **OpenAI兼容API Key**（如 [DeepSeek](https://platform.deepseek.com/)、[OpenAI](https://platform.openai.com/) 等）

### 安装部署

#### 方式一：Docker一键部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Sakura520222/Sakura-Channel-Summary-Assistant-Pro.git
cd Sakura-Channel-Summary-Assistant-Pro

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写您的配置

# 3. 启动服务
docker-compose up -d

# 4. 查看日志（首次运行需要Telegram登录）
docker-compose logs -f
```

#### 方式二：本地部署

```bash
# 1. 克隆项目
git clone https://github.com/Sakura520222/Sakura-Channel-Summary-Assistant-Pro.git
cd Sakura-Channel-Summary-Assistant-Pro

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写您的配置

# 4. 运行项目
python main.py
```

### 配置说明

#### 环境变量配置 (.env)

```env
# ===== Telegram配置 =====
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token

# ===== AI配置（支持任意OpenAI兼容API） =====
# 推荐使用DeepSeek（性价比高）
LLM_API_KEY=your_deepseek_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 或使用OpenAI
# LLM_API_KEY=your_openai_api_key
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-3.5-turbo

# ===== 管理员配置（支持多个ID，用逗号分隔） =====
REPORT_ADMIN_IDS=admin_id1,admin_id2

# ===== 日志级别配置 =====
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# ===== 投票功能配置 =====
ENABLE_POLL=True  # 是否启用投票功能，默认开启
```

#### 配置文件 (config.json)

系统会在首次运行时自动生成 `config.json` 文件，包含频道列表、时间配置等信息：

```json
{
  "channels": [
    "https://t.me/example_channel"
  ],
  "send_report_to_source": true,
  "enable_poll": true,
  "log_level": "INFO"
}
```

注意：AI配置只能通过 `.env` 文件配置，修改后需要重启机器人生效。

---

## 📋 功能详解

### 核心命令列表

#### 1. 基础命令 - 用户入门
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/start` | `/开始` | 查看欢迎消息和基本介绍 |
| `/help` | `/帮助` | 查看完整命令列表和使用说明 |
| `/changelog` | `/更新日志` | 查看项目更新日志 |

#### 2. 核心功能 - 主要功能
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/summary` | `/立即总结` | 立即生成频道消息汇总 |

#### 3. 频道管理 - 管理监控频道
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/showchannels` | `/查看频道列表` | 查看当前监控的频道列表 |
| `/addchannel` | `/添加频道` | 添加频道到监控列表 |
| `/deletechannel` | `/删除频道` | 从监控列表中删除频道 |

#### 4. 时间配置 - 自动总结时间
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/showchannelschedule` | `/查看频道时间配置` | 查看频道自动总结时间配置 |
| `/setchannelschedule` | `/设置频道时间配置` | 设置频道自动总结时间 |
| `/deletechannelschedule` | `/删除频道时间配置` | 删除频道自动总结时间配置 |
| `/clearsummarytime` | `/清除总结时间` | 清除上次总结时间记录 |
| `/setsendtosource` | `/设置报告发送回源频道` | 设置是否将报告发送回源频道 |

#### 5. 提示词配置 - AI提示词管理
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/showprompt` | `/查看提示词` | 查看当前使用的提示词 |
| `/setprompt` | `/设置提示词` | 设置自定义总结提示词 |
| `/showpollprompt` | `/查看投票提示词` | 查看当前投票提示词 |
| `/setpollprompt` | `/设置投票提示词` | 设置自定义投票提示词 |

#### 6. 投票配置 - 互动投票设置
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/channelpoll` | `/查看频道投票配置` | 查看频道投票配置 |
| `/setchannelpoll` | `/设置频道投票配置` | 设置频道投票配置 |
| `/deletechannelpoll` | `/删除频道投票配置` | 删除频道投票配置 |

#### 7. 历史记录 - 查看历史总结
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/history` | `/历史` | 查看历史总结记录 |
| `/export` | `/导出` | 导出历史记录为文件 |
| `/stats` | `/统计` | 查看频道统计数据 |

#### 8. 系统控制 - 机器人管理
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/pause` | `/暂停` | 暂停所有定时任务 |
| `/resume` | `/恢复` | 恢复所有定时任务 |
| `/restart` | `/重启` | 重启机器人服务 |
| `/shutdown` | `/关机` | 彻底停止机器人 |

#### 9. 日志与调试 - 系统维护
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/showloglevel` | `/查看日志级别` | 查看当前日志级别 |
| `/setloglevel` | `/设置日志级别` | 设置日志级别 |
| `/clearcache` | `/清除缓存` | 清除讨论组ID缓存 |
| `/cleanlogs` | `/清理日志` | 清理旧日志文件 |

#### 10. 黑名单管理（可选功能）
| 命令 | 别名 | 功能说明 |
|------|------|----------|
| `/blacklist` | `/黑名单` | 查看黑名单列表 |
| `/addblacklist` | `/添加黑名单` | 添加用户到黑名单 |
| `/removeblacklist` | `/移除黑名单` | 从黑名单移除用户 |
| `/clearblacklist` | `/清空黑名单` | 清空黑名单 |
| `/blackliststats` | `/黑名单统计` | 查看黑名单统计信息 |

**日志文件说明**：

每次启动机器人时，会在 `log/` 目录下创建基于时间戳的新目录，所有日志文件都在该目录中：

```
log/
├── 20260117_191530/        # 2026-01-17 19:15:30启动的会话
│   ├── console.log          # 控制台日志
│   ├── main.log            # 主程序日志
│   ├── telegram.log        # Telegram客户端日志
│   ├── ai_client.log       # AI客户端日志
│   ├── database.log        # 数据库操作日志
│   ├── scheduler.log       # 调度器日志
│   ├── command_handlers.log # 命令处理日志
│   ├── error.log           # 错误日志
│   ├── telegram_error.log   # Telegram错误日志
│   ├── ai_error.log        # AI错误日志
│   └── database_error.log  # 数据库错误日志
├── 20260117_193045/        # 2026-01-17 19:30:45启动的会话
│   └── ... (同样的日志文件)
└── archive/                   # 归档目录
```

**日志文件说明**：
- `console.log` - 记录所有控制台输出（包括print语句）
- `main.log` - 主程序日志
- `telegram.log` - Telegram客户端日志
- `ai_client.log` - AI客户端日志
- `database.log` - 数据库操作日志
- `scheduler.log` - 调度器日志
- `error.log` - 错误日志

### 详细使用说明

#### 历史记录功能

**查看历史总结**
```bash
# 查看所有频道最近10条总结
/history

# 查看指定频道最近10条总结
/history channel1

# 查看指定频道最近30天的总结
/history channel1 30

# 支持完整URL格式
/history https://t.me/channel1 7
```

**导出历史记录**
```bash
# 导出所有记录为JSON（默认格式）
/export

# 导出指定频道为JSON
/export channel1

# 导出为CSV格式（适合Excel）
/export channel1 csv

# 导出为md格式（适合阅读）
/export channel1 md
```

**查看统计数据**
```bash
# 查看所有频道的统计数据
/stats

# 查看指定频道的统计
/stats channel1
```

**统计信息包括**：
- 总总结次数、总处理消息数、平均消息数
- 按类型统计（日报/周报/手动总结）
- 时间分布（本周、本月总结次数）
- 最近总结时间
- 频道排行榜（按总结次数排序）

#### 频道时间配置

**每天模式**
```bash
/setchannelschedule FireflyLeak daily 23 0
# 含义：FireflyLeak频道每天23:00执行自动总结
```

**每周多天模式**
```bash
/setchannelschedule Nahida_Leak weekly mon,thu 14 30
# 含义：Nahida_Leak频道每周一和周四14:30执行自动总结
```

**传统每周单天模式**
```bash
/setchannelschedule FireflyLeak sun 9 0
# 含义：FireflyLeak频道每周日09:00执行自动总结
```

#### 频道投票配置

```bash
# 查看所有频道的投票配置
/channelpoll

# 设置频道投票：启用并发送到频道（回复总结消息）
/setchannelpoll channel1 true channel

# 设置频道投票：启用并发送到讨论组（回复转发消息）
/setchannelpoll channel1 true discussion

# 禁用频道投票功能
/setchannelpoll channel1 false channel

# 删除频道投票配置（恢复全局配置）
/deletechannelpoll channel1
```

---

## 🏗️ 技术架构

### 项目结构

```
Sakura-Channel-Summary-Assistant-Pro/
│
├── 📄 核心源代码文件
│   ├── main.py                    # 主程序入口
│   ├── config.py                  # 配置管理模块
│   ├── ai_client.py               # AI客户端模块
│   ├── telegram_client.py         # Telegram客户端模块
│   ├── telegram_client_utils.py   # Telegram客户端工具模块
│   ├── command_handlers.py        # 命令处理模块
│   ├── scheduler.py               # 调度器模块
│   ├── error_handler.py           # 错误处理模块
│   ├── prompt_manager.py          # 提示词管理模块
│   ├── poll_prompt_manager.py     # 投票提示词管理模块
│   ├── poll_regeneration_handlers.py  # 投票重新生成处理模块
│   ├── summary_time_manager.py    # 时间管理模块
│   ├── history_handlers.py        # 历史记录处理模块
│   ├── database.py                # 数据库管理模块
│   ├── restart_bot.py             # 机器人重启脚本
│   └── restart_bot_improved.py    # 改进版重启脚本
│
├── 📄 配置文件
│   ├── .env                       # 环境变量配置（从.env.example复制）
│   ├── .env.example               # 环境变量示例
│   ├── config.json                # AI配置文件（运行时生成）
│   ├── prompt.txt                 # 提示词文件（运行时生成）
│   ├── poll_prompt.txt            # 投票提示词文件（运行时生成）
│   └── .last_summary_time.json    # 时间记录文件（运行时生成）
│
├── � 会话文件（运行时生成）
│   ├── bot_session.session        # Telegram主会话
│   ├── health_check.session       # 健康检查会话
│   └── *.session-journal          # 会话日志文件
│
├── 📄 部署与构建文件
│   ├── Dockerfile                 # Docker镜像构建
│   ├── docker-compose.yml         # Docker Compose配置
│   ├── docker-entrypoint.sh       # Docker入口点脚本
│   ├── requirements.txt           # Python依赖
│   └── start.bat                  # Windows启动脚本
│
├── 📄 文档文件
│   ├── README.md                  # 项目说明文档
│   ├── CHANGELOG.md               # 更新日志
│   └── LICENSE                    # 许可证文件
│
└── 📁 data/                       # 数据目录
    └── summaries.db               # SQLite数据库文件
```

### 技术栈

| 技术 | 用途 | 版本 |
|------|------|------|
| **Python** | 主编程语言 | 3.13+ |
| **Telethon** | Telegram API客户端 | 1.34+ |
| **OpenAI SDK** | AI API调用 | 1.0+ |
| **APScheduler** | 定时任务调度 | 3.10+ |
| **SQLite** | 数据持久化 | 3.x |
| **Docker** | 容器化部署 | 20.10+ |
| **Docker Compose** | 容器编排 | 2.0+ |

### 核心模块说明

- **main.py**：程序入口，负责初始化和事件循环
- **config.py**：配置管理，处理环境变量和配置文件
- **ai_client.py**：AI客户端，处理AI API调用和响应
- **telegram_client.py**：Telegram客户端，处理消息抓取和发送
- **scheduler.py**：调度器，管理定时任务
- **command_handlers.py**：命令处理器，处理所有Telegram命令
- **database.py**：数据库管理，处理数据持久化
- **error_handler.py**：错误处理，提供重试和恢复机制

---

## 🐳 Docker部署

### 一键部署

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 数据持久化

容器使用本地卷进行数据持久化，所有重要数据都保存在本地文件系统中：

```
Sakura-Channel-Summary-Assistant-Pro/
├── 📄 配置文件（持久化保存）
│   ├── .env                    # 环境变量配置
│   ├── config.json             # AI配置文件
│   ├── prompt.txt              # 提示词文件
│   └── .last_summary_time.json # 总结时间记录文件
│
├── 📄 会话文件（持久化保存）
│   ├── bot_session.session     # Telegram主会话
│   ├── health_check.session    # 健康检查会话
│   └── *.session-journal       # 会话日志文件
│
└── 📄 数据库（持久化保存）
    └── data/summaries.db      # SQLite数据库文件
```

### 管理命令

```bash
# 进入容器
docker-compose exec sakura-summary-bot-pro bash

# 重启服务
docker-compose restart

# 更新服务（重新构建镜像）
docker-compose up -d --build

# 查看健康状态
docker inspect --format='{{json .State.Health}}' sakura-summary-bot-pro
```

---

## 📄 许可证

本项目采用 **GNU General Public License v3.0 (GPLv3)** 许可证。

### 许可证核心条款

**您可以：**
- ✅ **商业使用** - 将本软件用于商业目的
- ✅ **修改** - 修改本软件以满足您的需求
- ✅ **分发** - 分发本软件的副本
- ✅ **专利使用** - 明确授予专利许可

**您必须：**
- ⚠️ **开源修改** - 如果您修改了代码，必须开源修改后的代码
- ⚠️ **源代码分发** - 分发程序时必须同时提供源代码
- ⚠️ **相同许可证** - 修改和分发必须使用相同的GPLv3许可证
- ⚠️ **版权声明** - 保留原有的版权声明和许可证

### 商业模式建议

GPLv3许可证特别适合以下商业模式：

1. **托管服务**：提供SaaS托管服务，用户无需自己部署
2. **技术支持**：提供专业的安装、配置和维护服务
3. **定制开发**：为企业提供基于本项目的定制化解决方案
4. **咨询服务**：提供频道管理、AI调优等专业咨询服务
5. **培训服务**：提供产品使用和技术培训

**注意事项：**
- 分发修改后的代码时必须开源修改部分
- 必须向用户提供完整的源代码
- 不能将代码闭源或以其他许可证分发

---

## 📝 更新日志

查看完整更新日志：[CHANGELOG.md](CHANGELOG.md)

---

## 🤝 支持与服务

### 商业支持

我们提供专业的商业支持服务，包括：

- 🎯 **部署支持**：专业的一对一部署指导
- 🔧 **定制开发**：根据您的需求进行功能定制
- 📊 **数据分析**：深入的数据分析和优化建议
- 🎓 **培训服务**：团队培训和最佳实践指导
- 🛡️ **技术支持**：7x24小时技术支持和故障排查

### 联系方式

- 📧 **电子邮件**：[sakura520222@outlook.com](mailto:sakura520222@outlook.com)
- 🐛 **GitHub Issues**：[提交问题](https://github.com/Sakura520222/Sakura-Channel-Summary-Assistant-Pro/issues)

---

<div align="center">

**🌸 Sakura-频道总结助手** · 让频道管理更智能

[快速开始](#-快速开始) · [功能详解](#-功能详解) · [Docker部署](#-docker部署) · [许可证](#-许可证)

**Copyright © 2026 Sakura-Channel-Summary-Assistant-Pro. All Rights Reserved.**

</div>
