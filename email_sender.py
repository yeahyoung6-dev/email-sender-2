"""
邮件发送模块
支持SMTP发送HTML邮件，间隔控制
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from typing import Optional, Callable, Dict, Any, List, Tuple
import html
import os
import re
import threading


SMTP_TIMEOUT = 30  # SMTP连接/读写超时（秒）

# 判断模板是否为HTML（包含HTML标签）
_HTML_TAG_RE = re.compile(r'<\s*/?\s*[a-zA-Z][^>]*>')


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

        self._stop_event: Optional[threading.Event] = None
        self._thread: Optional[threading.Thread] = None

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

    def _connect(self) -> smtplib.SMTP:
        """建立SMTP连接并登录"""
        if self.use_ssl:
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=SMTP_TIMEOUT)
        else:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=SMTP_TIMEOUT)
        try:
            if not self.use_ssl:
                server.starttls()
            server.login(self.sender_email, self.sender_password)
        except Exception:
            self._close(server)
            raise
        return server

    @staticmethod
    def _close(server: Optional[smtplib.SMTP]) -> None:
        """关闭SMTP连接（忽略错误）"""
        if server is None:
            return
        try:
            server.quit()
        except Exception:
            try:
                server.close()
            except Exception:
                pass

    def test_connection(self) -> Dict[str, Any]:
        """测试SMTP连接"""
        try:
            server = self._connect()
            self._close(server)
            return {'success': True, 'message': '连接成功'}
        except smtplib.SMTPAuthenticationError:
            return {'success': False, 'message': '认证失败，请检查邮箱和授权码'}
        except smtplib.SMTPConnectError:
            return {'success': False, 'message': '无法连接到服务器，请检查服务器地址和端口'}
        except Exception as e:
            return {'success': False, 'message': f'连接失败: {str(e)}'}

    @staticmethod
    def is_html_template(template: str) -> bool:
        """判断模板是否包含HTML标签"""
        return bool(_HTML_TAG_RE.search(template))

    def render_template(self, template: str, data: Dict[str, Any],
                        escape_html: bool = False) -> str:
        """渲染模板，替换占位符"""
        result = template
        for key, value in data.items():
            placeholder = '{' + str(key) + '}'
            text = str(value) if value is not None else ''
            if escape_html:
                text = html.escape(text)
            result = result.replace(placeholder, text)
        return result

    def render_content(self, template: str, data: Dict[str, Any]) -> str:
        """渲染正文为HTML：HTML模板转义数据值；纯文本模板整体转义并保留换行"""
        if self.is_html_template(template):
            return self.render_template(template, data, escape_html=True)
        text = self.render_template(template, data)
        return html.escape(text).replace('\n', '<br>\n')

    @staticmethod
    def load_attachments(attachments: Optional[List[str]]) -> Tuple[List[Tuple[str, bytes]], List[str]]:
        """读取附件内容，返回 (附件列表[(文件名, 内容)], 缺失/无法读取的文件列表)"""
        loaded = []
        missing = []
        for file_path in attachments or []:
            try:
                with open(file_path, 'rb') as f:
                    loaded.append((os.path.basename(file_path), f.read()))
            except OSError:
                missing.append(file_path)
        return loaded, missing

    def _build_message(self, to_email: str, subject: str, content: str,
                       is_html: bool,
                       attachments: List[Tuple[str, bytes]]) -> MIMEMultipart:
        """构建邮件"""
        msg = MIMEMultipart('mixed')
        msg['From'] = formataddr((str(Header(self.sender_name, 'utf-8')), self.sender_email))
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Date'] = formatdate(localtime=True)
        domain = self.sender_email.rsplit('@', 1)[-1] or None
        msg['Message-ID'] = make_msgid(domain=domain)

        # 添加正文
        content_part = MIMEMultipart('alternative')
        content_type = 'html' if is_html else 'plain'
        content_part.attach(MIMEText(content, content_type, 'utf-8'))
        msg.attach(content_part)

        # 添加附件
        for filename, data in attachments:
            part = MIMEApplication(data)
            # 处理中文文件名
            part.add_header('Content-Disposition', 'attachment',
                            filename=('utf-8', '', filename))
            msg.attach(part)

        return msg

    def is_sending(self) -> bool:
        """是否有发送线程在运行"""
        return self._thread is not None and self._thread.is_alive()

    def send_batch(self, records: list, email_column: str,
                   subject_template: str, content_template: str,
                   attachments: List[str] = None,
                   progress_callback: Optional[Callable] = None,
                   complete_callback: Optional[Callable] = None) -> bool:
        """批量发送邮件（在后台线程运行），已有发送任务在运行时返回 False"""
        if self.is_sending():
            return False

        # 每次发送使用独立的停止事件，避免旧线程被新任务"复活"
        stop_event = threading.Event()
        self._stop_event = stop_event
        loaded_attachments, _ = self.load_attachments(attachments)

        def _send():
            total = len(records)
            success_count = 0
            fail_count = 0
            results = []
            server: Optional[smtplib.SMTP] = None
            stop_reason: Optional[str] = None

            try:
                for i, record in enumerate(records):
                    if stop_event.is_set():
                        stop_reason = '用户停止'
                        break

                    to_email = str(record.get(email_column, '') or '').strip()
                    if not to_email:
                        result = {'success': False, 'message': '邮箱为空'}
                    else:
                        subject = self.render_template(subject_template, record)
                        content = self.render_content(content_template, record)
                        msg = self._build_message(to_email, subject, content, True,
                                                  loaded_attachments)
                        try:
                            result, server = self._send_with_retry(server, to_email, msg)
                        except smtplib.SMTPAuthenticationError:
                            server = None
                            stop_reason = '认证失败，请检查邮箱和授权码'
                            result = {'success': False, 'message': '认证失败，已中止发送'}

                    result['email'] = to_email
                    result['index'] = i + 1
                    results.append(result)

                    if result['success']:
                        success_count += 1
                    else:
                        fail_count += 1

                    if progress_callback:
                        progress_callback(i + 1, total, result)

                    if stop_reason:
                        break

                    # 发送间隔（最后一封不等待，停止时立即唤醒）
                    if i < total - 1 and stop_event.wait(self.interval):
                        stop_reason = '用户停止'
                        break
            finally:
                self._close(server)
                if complete_callback:
                    complete_callback(success_count, fail_count, results, stop_reason)

        self._thread = threading.Thread(target=_send, daemon=True)
        self._thread.start()
        return True

    def _send_with_retry(self, server: Optional[smtplib.SMTP], to_email: str,
                         msg: MIMEMultipart) -> Tuple[Dict[str, Any], Optional[smtplib.SMTP]]:
        """复用连接发送；连接断开时重连重试一次。返回 (结果, 可继续使用的连接)
        认证失败时抛出 SMTPAuthenticationError，由调用方中止发送"""
        for attempt in range(2):
            try:
                if server is None:
                    server = self._connect()
                server.sendmail(self.sender_email, [to_email], msg.as_string())
                return {'success': True, 'message': '发送成功'}, server
            except smtplib.SMTPAuthenticationError:
                self._close(server)
                raise
            except smtplib.SMTPRecipientsRefused as e:
                # 收件人被拒绝，连接仍可用
                return {'success': False, 'message': f'收件人被拒绝: {e.recipients}'}, server
            except smtplib.SMTPResponseException as e:
                # 服务器拒绝该邮件，重置会话后继续使用连接
                try:
                    server.rset()
                except Exception:
                    self._close(server)
                    server = None
                return {'success': False, 'message': f'{e.smtp_code} {e.smtp_error!r}'}, server
            except (smtplib.SMTPServerDisconnected, OSError) as e:
                # 连接问题（断开/超时/网络错误）：丢弃连接，重连后重试一次
                self._close(server)
                server = None
                if attempt == 1:
                    return {'success': False, 'message': str(e)}, None
            except Exception as e:
                self._close(server)
                return {'success': False, 'message': str(e)}, None
        return {'success': False, 'message': '发送失败'}, server

    def stop_sending(self) -> None:
        """停止发送"""
        if self._stop_event is not None:
            self._stop_event.set()
