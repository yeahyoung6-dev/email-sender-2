"""
日志记录模块
记录发送结果到文件
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class SendLogger:
    """发送日志类"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.current_log_file: Optional[str] = None
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def create_session_log(self) -> str:
        """创建本次发送的日志文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(self.log_dir, f"send_log_{timestamp}.json")
        initial_data = {
            "start_time": datetime.now().isoformat(),
            "records": [],
            "summary": None
        }
        with open(self.current_log_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        return self.current_log_file

    def log_record(self, email: str, success: bool,
                   message: str, extra: Optional[Dict] = None) -> None:
        """记录单条发送结果"""
        if not self.current_log_file:
            return

        record = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "success": success,
            "message": message
        }
        if extra:
            record.update(extra)

        try:
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["records"].append(record)
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入日志失败: {e}")

    def log_summary(self, success_count: int, fail_count: int) -> None:
        """记录发送摘要"""
        if not self.current_log_file:
            return

        try:
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["summary"] = {
                "end_time": datetime.now().isoformat(),
                "success_count": success_count,
                "fail_count": fail_count,
                "total_count": success_count + fail_count
            }
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入摘要失败: {e}")

    def get_log_files(self) -> List[str]:
        """获取所有日志文件"""
        if not os.path.exists(self.log_dir):
            return []
        files = [f for f in os.listdir(self.log_dir) if f.startswith("send_log_") and f.endswith(".json")]
        return sorted(files, reverse=True)

    def read_log(self, filename: str) -> Optional[Dict[str, Any]]:
        """读取指定日志文件"""
        filepath = os.path.join(self.log_dir, filename)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def export_to_csv(self, log_filename: str, output_path: str) -> bool:
        """导出日志为CSV格式"""
        log_data = self.read_log(log_filename)
        if not log_data:
            return False

        try:
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['时间', '邮箱', '状态', '消息'])
                for record in log_data.get('records', []):
                    status = '成功' if record.get('success') else '失败'
                    writer.writerow([
                        record.get('timestamp', ''),
                        record.get('email', ''),
                        status,
                        record.get('message', '')
                    ])
            return True
        except Exception:
            return False