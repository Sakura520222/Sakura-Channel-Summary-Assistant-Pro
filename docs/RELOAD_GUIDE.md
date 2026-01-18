# 配置热重载运维指南

## 概述

Sakura 频道总结助手支持配置热重载功能，可以在不重启机器人的情况下更新配置。

## 支持热重载的配置项

| 配置文件 | 配置项 | 热重载支持 | 备注 |
|---------|---------|-----------|------|
| `.env` | `LOG_LEVEL` | ✅ 支持 | 日志级别实时更新 |
| `.env` | 其他环境变量 | ⚠️ 部分支持 | 大部分需要重启 |
| `data/config/config.json` | `channels` | ✅ 支持 | 自动重启调度器 |
| `data/config/config.json` | `summary_schedules` | ✅ 支持 | 自动重启调度器 |
| `data/config/config.json` | `channel_poll_settings` | ✅ 支持 | 实时生效 |
| `data/config/config.json` | 其他配置 | ✅ 支持 | 实时生效 |
| `data/config/prompt.txt` | 总结提示词 | ✅ 支持 | 下次生成总结时生效 |
| `data/config/poll_prompt.txt` | 投票提示词 | ✅ 支持 | 下次生成总结时生效 |

## 热重载模式

### 1. 自动模式（推荐）

当 `watchdog` 模块已安装时，系统会自动监控配置文件变化，2秒防抖后自动重载。

**启用自动监控：**
```bash
pip install watchdog>=3.0.0
```

**日志提示：**
```
✅ 配置热重载功能已启动（自动监控启用）
```

### 2. 手动模式（备用）

当 `watchdog` 未安装时，可以使用 `/reload` 命令手动触发重载。

**日志提示：**
```
⚠️ 配置热重载功能已禁用（watchdog 未安装），请使用 /reload 命令手动重载
```

## 手动重载命令

```bash
# 重载所有配置
/reload

# 只重载环境变量（日志级别）
/reload env

# 只重载配置文件（config.json）
/reload config

# 只重载提示词
/reload prompts
```

## Docker 部署注意事项

### 1. 挂载整个目录

**推荐做法：** 挂载整个 `data/config/` 目录，而不是单个文件。

```yaml
# ✅ 推荐：挂载整个目录
volumes:
  - ./data:/app/data

# ❌ 不推荐：只挂载单个文件（可能导致 watchdog 监控失效）
volumes:
  - ./data/config/config.json:/app/data/config/config.json
```

### 2. Inode 问题

在某些 Linux 内核上，使用 `vim` 等编辑器编辑文件会改变文件的 Inode，导致 watchdog 无法检测到变化。

**解决方案：**
- 使用挂载整个目录的方式（推荐）
- 使用 `sed` 或 `echo` 等不改变 Inode 的命令
- 修改文件后使用 `/reload` 命令手动触发重载

### 3. .env 文件热重载

如需在 Docker 中支持 .env 文件的热重载，请取消以下注释：

```yaml
volumes:
  # 挂载 .env 文件以支持热重载（可选）
  - ./.env:/app/.env:ro
```

**注意：** 使用 `:ro` 只读挂载更安全。

## 需要重启的配置

以下配置项修改后必须重启机器人才能生效：

| 配置项 | 说明 |
|-------|------|
| `API_ID` | Telegram API ID |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | 机器人 Token |
| `ADMIN_LIST` | 管理员列表 |

**重启方法：**
```bash
# 使用命令重启
/restart

# 或使用 Docker 重启
docker-compose restart
```

## 验证配置重载

### 查看当前配置状态

```bash
# 查看当前日志级别
/showloglevel

# 查看当前频道列表
/showchannels

# 查看当前提示词
/showprompt

# 查看当前配置状态（包含所有重载结果）
/reload
```

### 查看重载日志

配置重载后，系统会在日志中输出详细信息：

```
INFO - 开始重载配置文件: data/config/config.json
INFO - JSON配置重载成功: {'channels': 5, 'summary_schedules': 5, ...}
INFO - 调度器已重启
INFO - 新调度器已启动，共添加了 6 个定时任务
```

## 故障排查

### 自动监控不工作

**症状：** 修改配置文件后，日志中没有重载记录。

**原因：** `watchdog` 模块未安装。

**解决方法：**
```bash
pip install watchdog>=3.0.0
# 或
pip install -r requirements.txt
```

### Docker 中监控失效

**症状：** 在宿主机修改配置文件后，容器内没有检测到变化。

**原因：** 挂载方式不正确或文件系统不支持监控。

**解决方法：**
1. 检查是否挂载了整个目录
2. 尝试使用 `/reload` 命令手动触发
3. 考虑使用命名卷替代绑定挂载

### 配置重载失败

**症状：** 执行 `/reload` 命令后提示"配置验证失败"。

**原因：** 配置文件格式错误或数据无效。

**解决方法：**
1. 检查 JSON 格式是否正确（使用 JSON 验证工具）
2. 确保提示词文件非空
3. 查看日志中的详细错误信息

### 调度器未重启

**症状：** 修改频道或时间配置后，调度器没有重启。

**原因：** 配置文件监控失效。

**解决方法：**
```bash
# 手动重载配置
/reload config

# 或重启整个机器人
/restart
```

## 最佳实践

1. **生产环境建议：**
   - 启用自动监控（安装 watchdog）
   - 定期检查日志确认重载正常
   - 重要配置变更前先在测试环境验证

2. **配置变更流程：**
   - 修改配置文件
   - 等待 2-3 秒（自动监控）或执行 `/reload`
   - 查看日志确认重载成功
   - 验证配置是否生效

3. **监控建议：**
   - 监控日志中的"配置重载"相关消息
   - 定期执行 `/reload` 检查配置状态
   - 使用 `/showloglevel` 等命令验证配置

## 性能影响

- **内存开销：** watchdog 模块约占用 5-10MB 内存
- **CPU 开销：** 文件监控几乎不占用 CPU
- **IO 开销：** 配置重载时有短暂的 IO 读取

## 安全建议

1. **权限控制：** 热重载功能仅管理员可用
2. **配置备份：** 修改配置前建议备份
3. **文件权限：** 确保配置文件权限正确
4. **敏感信息：** .env 文件包含敏感信息，注意权限控制

## 常见问题

**Q: 热重载会影响正在进行的任务吗？**

A: 不会。调度器重启时会等待运行中的任务完成，确保不中断正在进行的总结任务。

**Q: 可以同时修改多个配置文件吗？**

A: 可以。防抖机制会确保在所有文件修改完成后才执行重载（默认 2 秒）。

**Q: 重载失败会影响现有配置吗？**

A: 不会。配置重载采用原子化操作，验证失败时不会修改现有配置。

**Q: Docker 中如何查看重载日志？**

A: 使用以下命令查看实时日志：
```bash
docker-compose logs -f sakura-summary-bot-pro | grep "重载"
```

**Q: 如何判断 watchdog 是否正常工作？**

A: 查看启动日志：
```
✅ 配置热重载功能已启动（自动监控启用）
```
或执行 `/reload` 命令查看监控状态。
