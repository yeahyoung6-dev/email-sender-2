"""
配置管理模块
保存和加载SMTP配置及其他设置
"""

import os
import sys
import json
import base64
import tempfile
from typing import Dict, Any, Optional


APP_NAME = "邮件群发工具"


def _is_writable(directory: str) -> bool:
    """实际创建临时文件检测目录是否可写（Windows 下 os.access 不可靠）"""
    try:
        with tempfile.TemporaryFile(dir=directory):
            pass
        return True
    except OSError:
        return False


def get_app_dir() -> str:
    """获取程序数据目录：优先 exe/脚本所在目录；不可写时（如装在 Program Files）使用用户目录"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后 __file__ 指向临时解压目录，需用 exe 所在目录
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    if _is_writable(base_dir):
        return base_dir

    fallback = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), APP_NAME)
    os.makedirs(fallback, exist_ok=True)
    return fallback


APP_DIR = get_app_dir()


class ConfigManager:
    """配置管理类"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(APP_DIR, "config.json")
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件；新位置没有配置时，兼容读取旧版保存在当前工作目录的配置"""
        path = self.config_file
        if not os.path.exists(path):
            legacy = os.path.abspath("config.json")
            if os.path.exists(legacy):
                path = legacy
            else:
                self.config = {}
                return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception:
            self.config = {}

    def _save_config(self) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def _encode(self, text: str) -> str:
        """简单编码（非加密，仅混淆）"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def _decode(self, encoded: str) -> str:
        """解码"""
        try:
            return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
        except Exception:
            return ""

    def get_smtp_config(self) -> Dict[str, Any]:
        """获取SMTP配置"""
        smtp = self.config.get('smtp', {})
        return {
            'server': smtp.get('server', ''),
            'port': smtp.get('port', 465),
            'email': smtp.get('email', ''),
            'password': self._decode(smtp.get('password', '')),
            'sender_name': smtp.get('sender_name', ''),
            'use_ssl': smtp.get('use_ssl', True)
        }

    def set_smtp_config(self, server: str, port: int, email: str,
                        password: str, sender_name: str = "",
                        use_ssl: bool = True) -> None:
        """设置SMTP配置"""
        self.config['smtp'] = {
            'server': server,
            'port': port,
            'email': email,
            'password': self._encode(password),
            'sender_name': sender_name or email,
            'use_ssl': use_ssl
        }
        self._save_config()

    def get_interval(self) -> float:
        """获取发送间隔"""
        return self.config.get('interval', 1.0)

    def set_interval(self, interval: float) -> None:
        """设置发送间隔"""
        self.config['interval'] = interval
        self._save_config()

    def get_last_excel(self) -> str:
        """获取上次使用的Excel文件路径"""
        return self.config.get('last_excel', '')

    def set_last_excel(self, path: str) -> None:
        """设置上次使用的Excel文件路径"""
        self.config['last_excel'] = path
        self._save_config()

    def get_last_email_column(self) -> str:
        """获取上次使用的邮箱列"""
        return self.config.get('last_email_column', '')

    def set_last_email_column(self, column: str) -> None:
        """设置上次使用的邮箱列"""
        self.config['last_email_column'] = column
        self._save_config()

    def get_templates(self) -> Dict[str, Dict[str, str]]:
        """获取保存的模板"""
        return self.config.get('templates', {})

    def save_template(self, name: str, subject: str, content: str) -> None:
        """保存模板"""
        if 'templates' not in self.config:
            self.config['templates'] = {}
        self.config['templates'][name] = {
            'subject': subject,
            'content': content
        }
        self._save_config()

    def delete_template(self, name: str) -> None:
        """删除模板"""
        if 'templates' in self.config and name in self.config['templates']:
            del self.config['templates'][name]
            self._save_config()