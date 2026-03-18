"""
GUI界面模块
Tkinter实现的主界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional
import os
import threading

from excel_handler import ExcelHandler
from email_sender import EmailSender
from config import ConfigManager
from logger import SendLogger


class EmailSenderGUI:
    """邮件群发工具GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("邮件群发工具")
        self.root.geometry("900x750")
        self.root.resizable(True, True)

        # 初始化组件
        self.excel_handler = ExcelHandler("")
        self.email_sender = EmailSender()
        self.config = ConfigManager()
        self.logger = SendLogger()

        # 状态变量
        self.is_sending = False
        self.current_excel_path = ""

        # 创建界面
        self._create_widgets()
        self._load_saved_config()

    def _create_widgets(self) -> None:
        """创建所有界面组件"""
        # 主容器，支持滚动
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === SMTP配置区域 ===
        smtp_frame = ttk.LabelFrame(main_frame, text="SMTP服务器配置", padding="10")
        smtp_frame.pack(fill=tk.X, pady=5)

        # 服务器地址
        row1 = ttk.Frame(smtp_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="服务器:", width=10).pack(side=tk.LEFT)
        self.smtp_server_var = tk.StringVar(value="smtp.qq.com")
        ttk.Entry(row1, textvariable=self.smtp_server_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="端口:").pack(side=tk.LEFT)
        self.smtp_port_var = tk.StringVar(value="465")
        ttk.Entry(row1, textvariable=self.smtp_port_var, width=8).pack(side=tk.LEFT, padx=5)
        self.use_ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row1, text="SSL", variable=self.use_ssl_var).pack(side=tk.LEFT, padx=5)

        # 邮箱和密码
        row2 = ttk.Frame(smtp_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="发件邮箱:", width=10).pack(side=tk.LEFT)
        self.sender_email_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.sender_email_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="授权码:").pack(side=tk.LEFT)
        self.sender_password_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.sender_password_var, width=20, show="*").pack(side=tk.LEFT, padx=5)

        # 发件人名称和测试按钮
        row3 = ttk.Frame(smtp_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="发件人名称:", width=10).pack(side=tk.LEFT)
        self.sender_name_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.sender_name_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(row3, text="测试连接", command=self._test_smtp_connection).pack(side=tk.LEFT, padx=10)
        ttk.Button(row3, text="保存配置", command=self._save_smtp_config).pack(side=tk.LEFT)

        # === Excel文件区域 ===
        excel_frame = ttk.LabelFrame(main_frame, text="Excel文件", padding="10")
        excel_frame.pack(fill=tk.X, pady=5)

        excel_row = ttk.Frame(excel_frame)
        excel_row.pack(fill=tk.X)
        ttk.Label(excel_row, text="文件路径:").pack(side=tk.LEFT)
        self.excel_path_var = tk.StringVar()
        ttk.Entry(excel_row, textvariable=self.excel_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(excel_row, text="浏览...", command=self._browse_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(excel_row, text="加载", command=self._load_excel).pack(side=tk.LEFT, padx=5)

        # 字段显示
        field_row = ttk.Frame(excel_frame)
        field_row.pack(fill=tk.X, pady=5)
        ttk.Label(field_row, text="字段列表:").pack(side=tk.LEFT)
        self.fields_var = tk.StringVar(value="请加载Excel文件")
        ttk.Label(field_row, textvariable=self.fields_var, foreground="blue").pack(side=tk.LEFT, padx=5)

        # 邮箱列选择
        email_col_row = ttk.Frame(excel_frame)
        email_col_row.pack(fill=tk.X, pady=2)
        ttk.Label(email_col_row, text="邮箱列:").pack(side=tk.LEFT)
        self.email_column_var = tk.StringVar()
        self.email_column_combo = ttk.Combobox(email_col_row, textvariable=self.email_column_var, width=20, state="readonly")
        self.email_column_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(email_col_row, text="发送间隔(秒):").pack(side=tk.LEFT, padx=10)
        self.interval_var = tk.StringVar(value="1")
        ttk.Entry(email_col_row, textvariable=self.interval_var, width=8).pack(side=tk.LEFT)

        # 数据预览
        ttk.Label(excel_frame, text="数据预览:").pack(anchor=tk.W)
        self.preview_text = scrolledtext.ScrolledText(excel_frame, height=4, width=80)
        self.preview_text.pack(fill=tk.X, pady=2)

        # === 邮件模板区域 ===
        template_frame = ttk.LabelFrame(main_frame, text="邮件模板", padding="10")
        template_frame.pack(fill=tk.X, pady=5)

        # 模板管理行
        tmpl_row = ttk.Frame(template_frame)
        tmpl_row.pack(fill=tk.X, pady=2)
        ttk.Label(tmpl_row, text="模板:").pack(side=tk.LEFT)
        self.template_name_var = tk.StringVar()
        self.template_combo = ttk.Combobox(tmpl_row, textvariable=self.template_name_var, width=20)
        self.template_combo.pack(side=tk.LEFT, padx=5)
        self.template_combo.bind('<<ComboboxSelected>>', self._load_template)
        ttk.Button(tmpl_row, text="保存模板", command=self._save_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(tmpl_row, text="删除模板", command=self._delete_template).pack(side=tk.LEFT, padx=5)

        # 邮件主题
        subject_row = ttk.Frame(template_frame)
        subject_row.pack(fill=tk.X, pady=2)
        ttk.Label(subject_row, text="主题:", width=10).pack(side=tk.LEFT)
        self.subject_var = tk.StringVar()
        ttk.Entry(subject_row, textvariable=self.subject_var, width=70).pack(side=tk.LEFT, padx=5)

        # 邮件内容
        ttk.Label(template_frame, text="内容 (支持HTML，使用{字段名}插入数据):").pack(anchor=tk.W, pady=2)
        self.content_text = scrolledtext.ScrolledText(template_frame, height=8, width=80)
        self.content_text.pack(fill=tk.X, pady=2)

        # 模板提示
        hint_label = ttk.Label(template_frame, text="示例: 尊敬的{name}，您好！您的订单号是{order_id}", foreground="gray")
        hint_label.pack(anchor=tk.W)

        # === 发送控制区域 ===
        control_frame = ttk.LabelFrame(main_frame, text="发送控制", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        btn_row = ttk.Frame(control_frame)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="预览首封", command=self._preview_first, width=12).pack(side=tk.LEFT, padx=5)
        self.send_btn = ttk.Button(btn_row, text="开始发送", command=self._start_send, width=12)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_row, text="停止发送", command=self._stop_send, width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="查看日志", command=self._show_logs, width=12).pack(side=tk.LEFT, padx=5)

        # 进度条
        progress_row = ttk.Frame(control_frame)
        progress_row.pack(fill=tk.X, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_row, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        self.progress_label = ttk.Label(progress_row, text="等待开始...")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        # 结果显示
        self.result_var = tk.StringVar(value="")
        ttk.Label(control_frame, textvariable=self.result_var, foreground="green").pack(anchor=tk.W)

        # 底部水印
        watermark_frame = ttk.Frame(self.root)
        watermark_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        ttk.Label(watermark_frame, text="Made by WangLin@人力资源部",
                  foreground="gray").pack()

        # 加载已保存的模板
        self._refresh_templates()

    def _load_saved_config(self) -> None:
        """加载已保存的配置"""
        smtp_config = self.config.get_smtp_config()
        if smtp_config['server']:
            self.smtp_server_var.set(smtp_config['server'])
            self.smtp_port_var.set(smtp_config['port'])
            self.sender_email_var.set(smtp_config['email'])
            self.sender_password_var.set(smtp_config['password'])
            self.sender_name_var.set(smtp_config['sender_name'])
            self.use_ssl_var.set(smtp_config['use_ssl'])

        interval = self.config.get_interval()
        if interval:
            self.interval_var.set(str(interval))

        last_excel = self.config.get_last_excel()
        if last_excel and os.path.exists(last_excel):
            self.excel_path_var.set(last_excel)
            self._load_excel()

    def _save_smtp_config(self) -> None:
        """保存SMTP配置"""
        self.config.set_smtp_config(
            server=self.smtp_server_var.get(),
            port=int(self.smtp_port_var.get()),
            email=self.sender_email_var.get(),
            password=self.sender_password_var.get(),
            sender_name=self.sender_name_var.get(),
            use_ssl=self.use_ssl_var.get()
        )
        messagebox.showinfo("成功", "配置已保存")

    def _test_smtp_connection(self) -> None:
        """测试SMTP连接"""
        self.email_sender.set_config(
            server=self.smtp_server_var.get(),
            port=int(self.smtp_port_var.get()),
            email=self.sender_email_var.get(),
            password=self.sender_password_var.get(),
            use_ssl=self.use_ssl_var.get()
        )
        result = self.email_sender.test_connection()
        if result['success']:
            messagebox.showinfo("成功", result['message'])
        else:
            messagebox.showerror("失败", result['message'])

    def _browse_excel(self) -> None:
        """浏览选择Excel文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            self.excel_path_var.set(file_path)
            self._load_excel()

    def _load_excel(self) -> None:
        """加载Excel文件"""
        file_path = self.excel_path_var.get()
        if not file_path:
            messagebox.showwarning("提示", "请选择Excel文件")
            return

        self.excel_handler = ExcelHandler(file_path)
        success, error_msg = self.excel_handler.load_file()
        if not success:
            messagebox.showerror("错误", error_msg)
            return

        # 显示字段
        columns = self.excel_handler.get_columns()
        self.fields_var.set(", ".join(columns))

        # 更新邮箱列下拉框
        self.email_column_combo['values'] = columns
        if self.excel_handler.email_column:
            self.email_column_var.set(self.excel_handler.email_column)
        elif columns:
            self.email_column_var.set(columns[0])

        # 显示预览
        preview_data = self.excel_handler.get_preview_data(3)
        preview_text = ""
        for i, record in enumerate(preview_data, 1):
            preview_text += f"第{i}行: {record}\n"
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', preview_text)

        # 保存路径
        self.config.set_last_excel(file_path)
        if self.email_column_var.get():
            self.config.set_last_email_column(self.email_column_var.get())

        messagebox.showinfo("成功", f"已加载 {self.excel_handler.get_row_count()} 条记录")

    def _refresh_templates(self) -> None:
        """刷新模板列表"""
        templates = self.config.get_templates()
        self.template_combo['values'] = list(templates.keys())

    def _save_template(self) -> None:
        """保存模板"""
        name = self.template_name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入模板名称")
            return

        self.config.save_template(
            name=name,
            subject=self.subject_var.get(),
            content=self.content_text.get('1.0', tk.END)
        )
        self._refresh_templates()
        messagebox.showinfo("成功", f"模板 '{name}' 已保存")

    def _load_template(self, event=None) -> None:
        """加载选中的模板"""
        name = self.template_name_var.get()
        templates = self.config.get_templates()
        if name in templates:
            self.subject_var.set(templates[name]['subject'])
            self.content_text.delete('1.0', tk.END)
            self.content_text.insert('1.0', templates[name]['content'])

    def _delete_template(self) -> None:
        """删除模板"""
        name = self.template_name_var.get()
        if not name:
            return
        if messagebox.askyesno("确认", f"确定删除模板 '{name}'？"):
            self.config.delete_template(name)
            self._refresh_templates()
            self.template_name_var.set("")

    def _preview_first(self) -> None:
        """预览第一封邮件"""
        if not self._validate_before_send():
            return

        records = self.excel_handler.get_records()
        if not records:
            messagebox.showwarning("提示", "没有数据可发送")
            return

        first_record = records[0]
        subject = self.email_sender.render_template(self.subject_var.get(), first_record)
        content = self.email_sender.render_template(self.content_text.get('1.0', tk.END), first_record)

        preview_window = tk.Toplevel(self.root)
        preview_window.title("邮件预览")
        preview_window.geometry("600x400")

        ttk.Label(preview_window, text=f"收件人: {first_record.get(self.email_column_var.get(), '')}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(preview_window, text=f"主题: {subject}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(preview_window, text="内容:").pack(anchor=tk.W, padx=10, pady=5)

        content_preview = scrolledtext.ScrolledText(preview_window, height=15, width=70)
        content_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        content_preview.insert('1.0', content)

    def _validate_before_send(self) -> bool:
        """发送前验证"""
        if not self.sender_email_var.get() or not self.sender_password_var.get():
            messagebox.showwarning("提示", "请填写发件邮箱和授权码")
            return False

        if not self.excel_handler.df is not None:
            messagebox.showwarning("提示", "请先加载Excel文件")
            return False

        if not self.email_column_var.get():
            messagebox.showwarning("提示", "请选择邮箱列")
            return False

        if not self.subject_var.get().strip():
            messagebox.showwarning("提示", "请填写邮件主题")
            return False

        content = self.content_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("提示", "请填写邮件内容")
            return False

        return True

    def _start_send(self) -> None:
        """开始发送"""
        if not self._validate_before_send():
            return

        # 验证邮箱
        email_col = self.email_column_var.get()
        validation = self.excel_handler.validate_emails()
        if not validation['valid']:
            msg = f"发现 {validation['invalid_count']} 个无效邮箱地址，是否继续发送？\n\n"
            msg += "无效邮箱（前5个）:\n"
            for item in validation['invalid_rows'][:5]:
                msg += f"  行{item['row']}: {item['email']}\n"
            if not messagebox.askyesno("警告", msg):
                return

        # 设置发送器配置
        self.email_sender.set_config(
            server=self.smtp_server_var.get(),
            port=int(self.smtp_port_var.get()),
            email=self.sender_email_var.get(),
            password=self.sender_password_var.get(),
            sender_name=self.sender_name_var.get(),
            interval=float(self.interval_var.get() or 1),
            use_ssl=self.use_ssl_var.get()
        )

        # 保存间隔设置
        self.config.set_interval(float(self.interval_var.get() or 1))

        # 创建日志
        self.logger.create_session_log()

        # 更新UI状态
        self.is_sending = True
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.result_var.set("")

        # 获取数据
        records = self.excel_handler.get_records()
        subject_template = self.subject_var.get()
        content_template = self.content_text.get('1.0', tk.END)

        # 定义回调函数
        def progress_callback(current, total, result):
            self.root.after(0, lambda: self._update_progress(current, total, result))

        def complete_callback(success, fail, results):
            self.root.after(0, lambda: self._on_send_complete(success, fail, results))

        # 开始批量发送
        self.email_sender.send_batch(
            records=records,
            email_column=email_col,
            subject_template=subject_template,
            content_template=content_template,
            is_html=True,
            progress_callback=progress_callback,
            complete_callback=complete_callback
        )

    def _update_progress(self, current: int, total: int, result: dict) -> None:
        """更新进度"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{current}/{total} - {result['email']}: {'成功' if result['success'] else '失败'}")

        # 记录日志
        self.logger.log_record(
            email=result['email'],
            success=result['success'],
            message=result['message']
        )

    def _on_send_complete(self, success: int, fail: int, results: list) -> None:
        """发送完成回调"""
        self.is_sending = False
        self.send_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="发送完成")

        # 记录摘要
        self.logger.log_summary(success, fail)

        total = success + fail
        self.result_var.set(f"发送完成: 成功 {success}/{total}, 失败 {fail}/{total}")

        if fail == 0:
            messagebox.showinfo("成功", f"全部发送成功！共 {success} 封邮件")
        else:
            messagebox.showwarning("完成", f"发送完成\n成功: {success}\n失败: {fail}")

    def _stop_send(self) -> None:
        """停止发送"""
        if messagebox.askyesno("确认", "确定停止发送？"):
            self.email_sender.stop_sending()
            self.is_sending = False
            self.send_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress_label.config(text="已停止")

    def _show_logs(self) -> None:
        """显示日志窗口"""
        log_window = tk.Toplevel(self.root)
        log_window.title("发送日志")
        log_window.geometry("700x500")

        # 日志文件列表
        log_files = self.logger.get_log_files()

        frame = ttk.Frame(log_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="选择日志文件:").pack(anchor=tk.W)

        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.X, pady=5)

        listbox = tk.Listbox(listbox_frame, height=5)
        listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        for f in log_files:
            listbox.insert(tk.END, f)

        # 日志内容显示
        ttk.Label(frame, text="日志内容:").pack(anchor=tk.W, pady=(10, 0))

        content_text = scrolledtext.ScrolledText(frame, height=15, width=80)
        content_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 导出按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)

        def load_log():
            selection = listbox.curselection()
            if not selection:
                return
            log_data = self.logger.read_log(log_files[selection[0]])
            if log_data:
                content_text.delete('1.0', tk.END)
                summary = log_data.get('summary', {})
                if summary:
                    content_text.insert(tk.END, f"=== 发送摘要 ===\n")
                    content_text.insert(tk.END, f"成功: {summary.get('success_count', 0)}\n")
                    content_text.insert(tk.END, f"失败: {summary.get('fail_count', 0)}\n\n")

                content_text.insert(tk.END, f"=== 发送记录 ===\n")
                for record in log_data.get('records', []):
                    status = '成功' if record.get('success') else '失败'
                    content_text.insert(tk.END,
                        f"{record.get('timestamp', '')} | {record.get('email', '')} | {status} | {record.get('message', '')}\n")

        def export_csv():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("提示", "请选择日志文件")
                return
            output_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv")]
            )
            if output_path:
                if self.logger.export_to_csv(log_files[selection[0]], output_path):
                    messagebox.showinfo("成功", f"已导出到 {output_path}")
                else:
                    messagebox.showerror("错误", "导出失败")

        ttk.Button(btn_frame, text="加载日志", command=load_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出CSV", command=export_csv).pack(side=tk.LEFT, padx=5)

    def run(self) -> None:
        """运行应用"""
        self.root.mainloop()