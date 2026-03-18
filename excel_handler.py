"""
Excel文件处理模块
支持读取xlsx/xls格式，提取字段名和数据
"""

import pandas as pd
from typing import Optional, List, Dict, Any
import re


class ExcelHandler:
    """Excel文件处理类"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df: Optional[pd.DataFrame] = None
        self.columns: List[str] = []
        self.email_column: Optional[str] = None

    def load_file(self) -> bool:
        """加载Excel文件"""
        try:
            if self.file_path.endswith('.xlsx'):
                self.df = pd.read_excel(self.file_path, engine='openpyxl')
            elif self.file_path.endswith('.xls'):
                self.df = pd.read_excel(self.file_path, engine='xlrd')
            else:
                return False

            self.columns = self.df.columns.tolist()
            self._detect_email_column()
            return True
        except Exception as e:
            print(f"加载Excel文件失败: {e}")
            return False

    def _detect_email_column(self) -> None:
        """自动检测邮箱列"""
        email_patterns = ['邮箱', 'email', 'e-mail', '邮件', 'email地址', '电子邮件']
        for col in self.columns:
            col_lower = str(col).lower()
            if any(pattern in col_lower for pattern in email_patterns):
                self.email_column = col
                break

        # 如果没找到，尝试检测内容是否符合邮箱格式
        if not self.email_column:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            for col in self.columns:
                sample = self.df[col].dropna().head(10).astype(str)
                if sample.str.match(email_regex).mean() > 0.8:
                    self.email_column = col
                    break

    def set_email_column(self, column_name: str) -> None:
        """手动设置邮箱列"""
        if column_name in self.columns:
            self.email_column = column_name

    def get_columns(self) -> List[str]:
        """获取所有列名"""
        return self.columns

    def get_row_count(self) -> int:
        """获取数据行数"""
        return len(self.df) if self.df is not None else 0

    def get_records(self) -> List[Dict[str, Any]]:
        """获取所有记录（字典列表）"""
        if self.df is None:
            return []
        return self.df.to_dict('records')

    def validate_emails(self) -> Dict[str, Any]:
        """验证邮箱地址"""
        if self.email_column is None or self.df is None:
            return {'valid': False, 'message': '未设置邮箱列'}

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_rows = []

        for idx, row in self.df.iterrows():
            email = str(row[self.email_column]).strip()
            if not re.match(email_regex, email):
                invalid_rows.append({'row': idx + 2, 'email': email})  # +2 因为Excel从1开始，且有表头

        return {
            'valid': len(invalid_rows) == 0,
            'invalid_count': len(invalid_rows),
            'invalid_rows': invalid_rows,
            'total_count': len(self.df)
        }

    def get_preview_data(self, count: int = 3) -> List[Dict[str, Any]]:
        """获取预览数据"""
        if self.df is None:
            return []
        return self.df.head(count).to_dict('records')