# 邮件群发工具

一个简单易用的邮件群发工具，支持从Excel读取收件人信息，自定义邮件模板，点对点发送邮件。

## 功能特点

- 📧 支持HTML格式邮件
- 📊 从Excel文件读取收件人数据
- 📝 自定义邮件模板，支持字段占位符
- ⏱️ 可配置发送间隔，防止被识别为垃圾邮件
- 📝 发送日志记录，支持导出CSV
- 💾 自动保存SMTP配置和模板
- 🖥️ 打包为单个exe文件，无需安装Python

## 快速开始

### 方式一：直接运行exe（推荐）

1. 下载 `邮件群发工具.exe`
2. 双击运行即可

### 方式二：从源码运行

1. 安装Python 3.8+
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行：
   ```bash
   python main.py
   ```

## 使用说明

### 1. 配置SMTP服务器

常用邮箱SMTP配置：

| 邮箱 | SMTP服务器 | 端口 | SSL |
|------|-----------|------|-----|
| QQ邮箱 | smtp.qq.com | 465 | 是 |
| 163邮箱 | smtp.163.com | 465 | 是 |
| Gmail | smtp.gmail.com | 587 | 否(STARTTLS) |
| Outlook | smtp.office365.com | 587 | 否(STARTTLS) |

**注意**：QQ邮箱、163邮箱等需要使用**授权码**而非登录密码。授权码需在邮箱设置中开启。

### 2. 准备Excel文件

Excel文件需包含邮箱地址列，例如：

| 姓名 | 邮箱 | 订单号 | 金额 |
|------|------|--------|------|
| 张三 | zhangsan@example.com | ORD001 | 100 |
| 李四 | lisi@example.com | ORD002 | 200 |

### 3. 编写邮件模板

使用 `{字段名}` 作为占位符，系统会自动替换为Excel中对应的数据。

**主题示例**：
```
您好，{姓名}，您的订单已确认
```

**内容示例（HTML）**：
```html
<p>尊敬的{name}，您好！</p>
<p>您的订单号是：{订单号}</p>
<p>订单金额：{金额}元</p>
<p>感谢您的支持！</p>
```

### 4. 发送邮件

1. 点击"加载"按钮加载Excel文件
2. 选择邮箱列
3. 设置发送间隔（建议1-3秒）
4. 点击"预览首封"检查效果
5. 点击"开始发送"

## 自动构建（GitHub Actions）

本项目支持通过 GitHub Actions 自动构建 Windows exe 文件。

### 方式一：发布新版本（推荐）

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub 会自动构建并创建 Release，可在 Releases 页面下载 `邮件群发工具.exe`。

### 方式二：手动触发

1. 进入 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Build Windows Executable** 工作流
4. 点击 **Run workflow**

构建完成后，在 **Artifacts** 中下载 `email-sender-windows`。

---

## 手动打包（Windows本地）

如果你在 Windows 电脑上，也可以本地打包：

```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name "邮件群发工具" main.py
```

生成的 exe 文件位于 `dist/邮件群发工具.exe`。

## 常见问题

### Q: 发送失败，提示认证错误？
A: 请确认使用的是授权码而非登录密码。QQ邮箱授权码获取方式：设置 → 账户 → POP3/SMTP服务 → 生成授权码

### Q: 邮件被拦截或进入垃圾箱？
A: 建议设置发送间隔为2-5秒，避免短时间内发送大量邮件。

### Q: 支持哪些Excel格式？
A: 支持 `.xlsx` 和 `.xls` 格式。

## 许可证

MIT License