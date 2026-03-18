"""
配置管理模块
保存和加载SMTP配置及其他设置
"""

import os
import json
import base64
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理类"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
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