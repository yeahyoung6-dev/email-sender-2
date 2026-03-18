"""
邮件发送模块
支持SMTP发送HTML邮件，间隔控制
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional, Callable, Dict, Any
import time
import threading


class EmailSender:
    """邮件发送类"""

    def __init__(self):
        self.smtp_server: str = ""
        self.smtp_port: int = 465
        self.sender_email: str = ""
        self.sender_password: str = ""
        self.sender_name: str = ""
        self.interval: float = 1.0  # 发送间隔（秒）
        self.use_ssl: bool = True

        self._stop_flag: bool = False
        self._connection: Optional[smtplib.SMTP] = None

    def set_config(self, server: str, port: int, email: str,
                   password: str, sender_name: str = "",
                   interval: float = 1.0, use_ssl: bool = True) -> None:
        """设置SMTP配置"""
        self.smtp_server = server
        self.smtp_port = port
        self.sender_email = email
        self.sender_password = password
        self.sender_name = sender_name or email
        self.interval = interval
        self.use_ssl = use_ssl

    def test_connection(self) -> Dict[str, Any]:
        """测试SMTP连接"""
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.sender_email, self.sender_password)
            server.quit()
            return {'success': True, 'message': '连接成功'}
        except smtplib.SMTPAuthenticationError:
            return {'success': False, 'message': '认证失败，请检查邮箱和授权码'}
        except smtplib.SMTPConnectError:
            return {'success': False, 'message': '无法连接到服务器，请检查服务器地址和端口'}
        except Exception as e:
            return {'success': False, 'message': f'连接失败: {str(e)}'}

    def render_template(self, template: str, data: Dict[str, Any]) -> str:
        """渲染模板，替换占位符"""
        result = template
        for key, value in data.items():
            placeholder = '{' + str(key) + '}'
            result = result.replace(placeholder, str(value) if value is not None else '')
        return result

    def send_single_email(self, to_email: str, subject: str,
                          content: str, is_html: bool = True) -> Dict[str, Any]:
        """发送单封邮件"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')

            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(content, content_type, 'utf-8'))

            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, to_email, msg.as_string())
            server.quit()

            return {'success': True, 'message': '发送成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def send_batch(self, records: list, email_column: str,
                   subject_template: str, content_template: str,
                   is_html: bool = True,
                   progress_callback: Optional[Callable] = None,
                   complete_callback: Optional[Callable] = None) -> None:
        """批量发送邮件（在后台线程运行）"""
        self._stop_flag = False

        def _send():
            total = len(records)
            success_count = 0
            fail_count = 0
            results = []

            for i, record in enumerate(records):
                if self._stop_flag:
                    break

                to_email = str(record.get(email_column, '')).strip()
                subject = self.render_template(subject_template, record)
                content = self.render_template(content_template, record)

                result = self.send_single_email(to_email, subject, content, is_html)
                result['email'] = to_email
                result['index'] = i + 1
                results.append(result)

                if result['success']:
                    success_count += 1
                else:
                    fail_count += 1

                if progress_callback:
                    progress_callback(i + 1, total, result)

                # 发送间隔（最后一封不等待）
                if i < total - 1 and not self._stop_flag:
                    time.sleep(self.interval)

            if complete_callback:
                complete_callback(success_count, fail_count, results)

        thread = threading.Thread(target=_send)
        thread.daemon = True
        thread.start()

    def stop_sending(self) -> None:
        """停止发送"""
        self._stop_flag = True