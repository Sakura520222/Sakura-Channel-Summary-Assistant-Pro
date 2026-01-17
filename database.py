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

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# 导入数据库路径配置
from config import DATABASE_PATH


class DatabaseManager:
    """总结历史记录数据库管理器"""

    def __init__(self, db_path=None):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        self.db_path = db_path if db_path else DATABASE_PATH
        self.init_database()
        logger.info(f"数据库管理器初始化完成: {self.db_path}")

    def init_database(self):
        """初始化数据库和表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建总结记录主表
            self._create_summaries_table(cursor)

            # 创建索引以提升查询性能
            self._create_indexes(cursor)

            # 创建数据库版本管理表
            self._create_version_table(cursor)

            # 插入或更新版本号
            self._update_database_version(cursor)

            conn.commit()
            conn.close()

            logger.info("数据库表结构初始化成功")

        except Exception as e:
            logger.error(f"初始化数据库失败: {type(e).__name__}: {e}", exc_info=True)
            raise

    def _create_summaries_table(self, cursor):
        """
        创建总结记录主表

        Args:
            cursor: 数据库游标
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                channel_name TEXT,
                summary_text TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ai_model TEXT,
                summary_type TEXT DEFAULT 'weekly',
                summary_message_ids TEXT,
                poll_message_id INTEGER,
                button_message_id INTEGER
            )
        """)

    def _create_indexes(self, cursor):
        """
        创建数据库索引

        Args:
            cursor: 数据库游标
        """
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_channel_created
            ON summaries(channel_id, created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created
            ON summaries(created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_channel
            ON summaries(channel_id)
        """)

    def _create_version_table(self, cursor):
        """
        创建数据库版本管理表

        Args:
            cursor: 数据库游标
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY,
                upgraded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _update_database_version(self, cursor):
        """
        更新数据库版本号

        Args:
            cursor: 数据库游标
        """
        cursor.execute("""
            INSERT OR REPLACE INTO db_version (version, upgraded_at)
            VALUES (1, CURRENT_TIMESTAMP)
        """)

    def save_summary(self, channel_id: str, channel_name: str, summary_text: str,
                     message_count: int, start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     summary_message_ids: Optional[List[int]] = None,
                     poll_message_id: Optional[int] = None,
                     button_message_id: Optional[int] = None,
                     ai_model: str = "unknown", summary_type: str = "weekly"):
        """
        保存总结记录到数据库

        Args:
            channel_id: 频道URL
            channel_name: 频道名称
            summary_text: 总结内容
            message_count: 消息数量
            start_time: 总结起始时间
            end_time: 总结结束时间
            summary_message_ids: 总结消息ID列表
            poll_message_id: 投票消息ID
            button_message_id: 按钮消息ID
            ai_model: AI模型名称
            summary_type: 总结类型 (daily/weekly/manual)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 准备数据
            summary_ids_json = json.dumps(summary_message_ids) if summary_message_ids else None
            start_time_str = start_time.isoformat() if start_time else None
            end_time_str = end_time.isoformat() if end_time else None

            # 插入记录
            summary_id = self._insert_summary_record(
                cursor, channel_id, channel_name, summary_text, message_count,
                start_time_str, end_time_str, ai_model, summary_type,
                summary_ids_json, poll_message_id, button_message_id
            )

            conn.commit()
            conn.close()

            logger.info(f"成功保存总结记录到数据库, ID: {summary_id}, 频道: {channel_name}")
            return summary_id

        except Exception as e:
            logger.error(f"保存总结记录失败: {type(e).__name__}: {e}", exc_info=True)
            return None

    def _insert_summary_record(self, cursor, channel_id, channel_name, summary_text,
                             message_count, start_time_str, end_time_str,
                             ai_model, summary_type, summary_ids_json,
                             poll_message_id, button_message_id):
        """
        插入总结记录到数据库

        Args:
            cursor: 数据库游标
            其他参数: 总结记录数据

        Returns:
            int: 新记录ID
        """
        cursor.execute("""
            INSERT INTO summaries (
                channel_id, channel_name, summary_text, message_count,
                start_time, end_time, ai_model, summary_type,
                summary_message_ids, poll_message_id, button_message_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            channel_id, channel_name, summary_text, message_count,
            start_time_str, end_time_str, ai_model, summary_type,
            summary_ids_json, poll_message_id, button_message_id
        ))
        return cursor.lastrowid

    def get_summaries(self, channel_id: Optional[str] = None, limit: int = 10,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        查询历史总结

        Args:
            channel_id: 可选，频道URL，不指定则查询所有频道
            limit: 返回记录数量，默认10条
            start_date: 可选，起始日期
            end_date: 可选，结束日期

        Returns:
            总结记录列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用字典格式返回结果
            cursor = conn.cursor()

            # 构建查询条件
            where_clause, params = self._build_query_conditions(
                channel_id, start_date, end_date
            )

            # 执行查询
            query = f"""
                SELECT * FROM summaries
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(limit)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            # 转换为字典列表
            summaries = self._convert_rows_to_summaries(rows)

            logger.info(f"查询到 {len(summaries)} 条总结记录")
            return summaries

        except Exception as e:
            logger.error(f"查询总结记录失败: {type(e).__name__}: {e}", exc_info=True)
            return []

    def _build_query_conditions(self, channel_id: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> tuple:
        """
        构建查询条件

        Args:
            channel_id: 频道URL
            start_date: 起始日期
            end_date: 结束日期

        Returns:
            tuple: (where_clause, params)
        """
        conditions = []
        params = []

        if channel_id:
            conditions.append("channel_id = ?")
            params.append(channel_id)

        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date.isoformat())

        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params

    def _convert_rows_to_summaries(self, rows: List) -> List[Dict[str, Any]]:
        """
        将数据库行转换为总结字典列表

        Args:
            rows: 数据库行列表

        Returns:
            总结字典列表
        """
        summaries = []
        for row in rows:
            summary = dict(row)

            # 解析JSON字段
            if summary['summary_message_ids']:
                try:
                    summary['summary_message_ids'] = json.loads(summary['summary_message_ids'])
                except:
                    summary['summary_message_ids'] = []
            else:
                summary['summary_message_ids'] = []

            summaries.append(summary)

        return summaries

    def get_summary_by_id(self, summary_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单条总结

        Args:
            summary_id: 总结记录ID

        Returns:
            总结记录字典，不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM summaries WHERE id = ?", (summary_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                summary = dict(row)
                # 解析JSON字段
                if summary['summary_message_ids']:
                    try:
                        summary['summary_message_ids'] = json.loads(summary['summary_message_ids'])
                    except:
                        summary['summary_message_ids'] = []
                else:
                    summary['summary_message_ids'] = []

                return summary
            return None

        except Exception as e:
            logger.error(f"查询总结记录失败 (ID={summary_id}): {type(e).__name__}: {e}", exc_info=True)
            return None

    def delete_old_summaries(self, days: int = 90) -> int:
        """
        删除旧总结记录

        Args:
            days: 保留天数，默认90天

        Returns:
            删除的记录数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)

            cursor.execute("""
                DELETE FROM summaries
                WHERE created_at < ?
            """, (cutoff_date.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"已删除 {deleted_count} 条旧总结记录 (超过 {days} 天)")
            return deleted_count

        except Exception as e:
            logger.error(f"删除旧总结记录失败: {type(e).__name__}: {e}", exc_info=True)
            return 0

    def _get_total_count(self, cursor, channel_condition: str, params: List) -> int:
        """获取总结总数"""
        cursor.execute(f"""
            SELECT COUNT(*) FROM summaries
            {channel_condition}
        """, params)
        return cursor.fetchone()[0]

    def _get_type_stats(self, cursor, channel_condition: str, params: List) -> Dict:
        """按类型统计总结"""
        cursor.execute(f"""
            SELECT summary_type, COUNT(*) as count
            FROM summaries
            {channel_condition}
            GROUP BY summary_type
        """, params)
        return dict(cursor.fetchall())

    def _get_total_messages(self, cursor, channel_condition: str, params: List) -> int:
        """获取总消息数"""
        cursor.execute(f"""
            SELECT SUM(message_count) FROM summaries
            {channel_condition}
        """, params)
        return cursor.fetchone()[0] or 0

    def _get_last_summary_time(self, cursor, channel_condition: str, params: List):
        """获取最近总结时间"""
        cursor.execute(f"""
            SELECT MAX(created_at) FROM summaries
            {channel_condition}
        """, params)
        return cursor.fetchone()[0]

    def _get_period_count(self, cursor, channel_id: Optional[str], days: int) -> int:
        """获取指定时间段的总结数"""
        date_ago = (datetime.now() - timedelta(days=days)).isoformat()
        if channel_id:
            cursor.execute("""
                SELECT COUNT(*) FROM summaries
                WHERE channel_id = ? AND created_at >= ?
            """, [channel_id, date_ago])
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM summaries
                WHERE created_at >= ?
            """, [date_ago])
        return cursor.fetchone()[0]

    def get_statistics(self, channel_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            channel_id: 可选，频道URL，不指定则统计所有频道

        Returns:
            统计信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 构建查询条件
            channel_condition = "WHERE channel_id = ?" if channel_id else ""
            params = [channel_id] if channel_id else []

            # 获取基础统计
            basic_stats = self._get_basic_statistics(cursor, channel_condition, params)
            
            # 获取时间段统计
            period_stats = self._get_period_statistics(cursor, channel_id)

            conn.close()

            # 合并统计结果
            stats = {**basic_stats, **period_stats}

            logger.info(f"统计数据获取成功: {stats}")
            return stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {type(e).__name__}: {e}", exc_info=True)
            return {}

    def _get_basic_statistics(self, cursor, channel_condition: str, params: List) -> Dict[str, Any]:
        """
        获取基础统计信息

        Args:
            cursor: 数据库游标
            channel_condition: 频道条件子句
            params: 查询参数

        Returns:
            基础统计字典
        """
        total_count = self._get_total_count(cursor, channel_condition, params)
        type_stats = self._get_type_stats(cursor, channel_condition, params)
        total_messages = self._get_total_messages(cursor, channel_condition, params)
        avg_messages = total_messages / total_count if total_count > 0 else 0
        last_summary_time = self._get_last_summary_time(cursor, channel_condition, params)

        return {
            "total_count": total_count,
            "type_stats": type_stats,
            "total_messages": total_messages,
            "avg_messages": round(avg_messages, 1),
            "last_summary_time": last_summary_time
        }

    def _get_period_statistics(self, cursor, channel_id: Optional[str]) -> Dict[str, int]:
        """
        获取时间段统计信息

        Args:
            cursor: 数据库游标
            channel_id: 频道URL

        Returns:
            时间段统计字典
        """
        week_count = self._get_period_count(cursor, channel_id, 7)
        month_count = self._get_period_count(cursor, channel_id, 30)

        return {
            "week_count": week_count,
            "month_count": month_count
        }

    def get_channel_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取频道排行(按总结次数)

        Args:
            limit: 返回记录数量

        Returns:
            频道排行列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    channel_id,
                    channel_name,
                    COUNT(*) as summary_count,
                    SUM(message_count) as total_messages
                FROM summaries
                GROUP BY channel_id, channel_name
                ORDER BY summary_count DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            ranking = [dict(row) for row in rows]
            logger.info(f"频道排行获取成功: {len(ranking)} 个频道")
            return ranking

        except Exception as e:
            logger.error(f"获取频道排行失败: {type(e).__name__}: {e}", exc_info=True)
            return []

    def export_summaries(self, output_format: str = "json",
                         channel_id: Optional[str] = None) -> Optional[str]:
        """
        导出历史记录

        Args:
            output_format: 输出格式 (json/csv/md)
            channel_id: 可选，频道URL，不指定则导出所有频道

        Returns:
            导出文件的路径，失败返回None
        """
        try:
            # 查询数据
            summaries = self.get_summaries(channel_id=channel_id, limit=10000)

            if not summaries:
                logger.warning("没有数据可导出")
                return None

            # 生成文件名
            filename = self._generate_export_filename(channel_id, output_format)

            # 执行导出
            success = self._execute_export(summaries, filename, output_format)
            
            if not success:
                return None

            logger.info(f"成功导出 {len(summaries)} 条记录到 {filename}")
            return filename

        except Exception as e:
            logger.error(f"导出历史记录失败: {type(e).__name__}: {e}", exc_info=True)
            return None

    def _generate_export_filename(self, channel_id: Optional[str], output_format: str) -> str:
        """
        生成导出文件名

        Args:
            channel_id: 频道URL
            output_format: 输出格式

        Returns:
            str: 文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        channel_suffix = f"_{channel_id.split('/')[-1]}" if channel_id else ""
        return f"summaries_export{channel_suffix}_{timestamp}.{output_format}"

    def _execute_export(self, summaries: List[Dict], filename: str, output_format: str) -> bool:
        """
        执行导出操作

        Args:
            summaries: 总结列表
            filename: 文件名
            output_format: 输出格式

        Returns:
            bool: 是否成功
        """
        if output_format == "json":
            self._export_json(summaries, filename)
        elif output_format == "csv":
            self._export_csv(summaries, filename)
        elif output_format == "md":
            self._export_md(summaries, filename)
        else:
            logger.error(f"不支持的导出格式: {output_format}")
            return False
        return True

    def _export_json(self, summaries: List[Dict], filename: str):
        """导出为JSON格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)

    def _export_csv(self, summaries: List[Dict], filename: str):
        """导出为CSV格式"""
        import csv

        if not summaries:
            return

        # 获取所有字段名
        fieldnames = list(summaries[0].keys())

        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for summary in summaries:
                # 将列表字段转换为字符串
                row = summary.copy()
                if isinstance(row.get('summary_message_ids'), list):
                    row['summary_message_ids'] = json.dumps(row['summary_message_ids'])
                writer.writerow(row)

    def _export_md(self, summaries: List[Dict], filename: str):
        """导出为md格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 频道总结历史记录\n\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"总记录数: {len(summaries)}\n\n")
            f.write("---\n\n")

            for summary in summaries:
                channel_name = summary.get('channel_name', summary.get('channel_id', '未知频道'))
                created_at = summary.get('created_at', '未知时间')
                summary_type = summary.get('summary_type', 'unknown')
                message_count = summary.get('message_count', 0)
                summary_text = summary.get('summary_text', '')

                # 类型中文映射
                type_map = {'daily': '日报', 'weekly': '周报', 'manual': '手动总结'}
                type_cn = type_map.get(summary_type, summary_type)

                f.write(f"## {channel_name} - {created_at} ({type_cn})\n\n")
                f.write(f"**消息数量**: {message_count}\n\n")
                f.write(f"**总结内容**:\n\n{summary_text}\n\n")
                f.write("---\n\n")


# 创建全局数据库管理器实例
db_manager = None

def get_db_manager():
    """获取全局数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
