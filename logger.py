"""
日志记录模块
记录发送结果到文件
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import APP_DIR


class SendLogger:
    """发送日志类"""

    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or os.path.join(APP_DIR, "logs")
        self.current_log_file: Optional[str] = None
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def create_session_log(self) -> str:
        """创建本次发送的日志文件（JSON Lines 格式，每行一条，只追加写入）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(self.log_dir, f"send_log_{timestamp}.jsonl")
        self._append({"type": "start", "start_time": datetime.now().isoformat()}, mode='w')
        return self.current_log_file

    def _append(self, entry: Dict[str, Any], mode: str = 'a') -> None:
        """追加一行日志"""
        try:
            with open(self.current_log_file, mode, encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"写入日志失败: {e}")

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
        record["type"] = "record"
        self._append(record)

    def log_summary(self, success_count: int, fail_count: int) -> None:
        """记录发送摘要"""
        if not self.current_log_file:
            return

        self._append({
            "type": "summary",
            "end_time": datetime.now().isoformat(),
            "success_count": success_count,
            "fail_count": fail_count,
            "total_count": success_count + fail_count
        })

    def get_log_files(self) -> List[str]:
        """获取所有日志文件（兼容旧版 .json 日志）"""
        if not os.path.exists(self.log_dir):
            return []
        files = [f for f in os.listdir(self.log_dir)
                 if f.startswith("send_log_") and (f.endswith(".jsonl") or f.endswith(".json"))]
        return sorted(files, reverse=True)

    def read_log(self, filename: str) -> Optional[Dict[str, Any]]:
        """读取指定日志文件，返回 {start_time, records, summary}"""
        filepath = os.path.join(self.log_dir, filename)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if not filename.endswith(".jsonl"):
                    return json.load(f)

                data: Dict[str, Any] = {"start_time": None, "records": [], "summary": None}
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except ValueError:
                        continue  # 跳过写入中断的残行
                    entry_type = entry.pop("type", "record")
                    if entry_type == "start":
                        data["start_time"] = entry.get("start_time")
                    elif entry_type == "summary":
                        data["summary"] = entry
                    else:
                        data["records"].append(entry)
                return data
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