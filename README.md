# Buildroom

论坛与 AI coding 项目展示的可运行雏形，暂用 **Buildroom** 作为站名。

使用 Python 3.12+、Django 5.2 LTS、Django 模板、HTMX 和 SQLite。前端无需构建工具，HTMX 随项目本地提供。

## 启动

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo  # 可选：添加虚构演示内容
.venv/bin/python manage.py runserver -6 '[::]:8710'
```

监听所有 IPv4 和 IPv6 网卡的 8710 端口；当前 Linux 的 `net.ipv6.bindv6only=0`，因此 `[::]` 同时接受 IPv4 连接。Django 的 `ALLOWED_HOSTS = ["*"]` 接受任意 IP 和域名。

本机打开 http://127.0.0.1:8710/ 或 http://[::1]:8710/；外部使用 `http://服务器IPv4:8710/`、`http://[服务器IPv6]:8710/` 或指向服务器的域名，网络防火墙需允许 TCP 8710。点击右上角注册即可体验发布与互动。示例作者不能登录，没有预设管理员或公开密码。

## 已实现

- **论坛**：杂谈、作品分享、求助、开发记录；发帖、作者编辑、回复、点赞、分类、搜索、排序与分页。
- **论坛界面**：以知乎式标题和正文摘要为主，结合 Reddit 式分类导航；信息流可直接点赞、进入回复或查看关联项目，手机端使用横向分类菜单。
- **项目**：发布和编辑介绍，记录 AI 工具，提供可选的演示与外部源码链接；分类、搜索与点赞。
- **项目讨论区**：每个项目可以关联多篇主题帖，帖子同时出现在公共论坛中。支持从项目创建讨论，以及在论坛按项目筛选。
- **账号**：Django 会话认证、用户名密码注册与登录，写入操作要求登录，编辑限作者本人。
- **语言**：默认英文，可切换简体中文；导航、表单、提示和日期随语言变化，用户内容保留原文。
- **内容**：正文支持 Markdown、代码块和表格，禁用原始 HTML；数据库保存所有发布内容。
- **管理**：复用 Django 管理后台。需要管理员时运行 `manage.py createsuperuser`，访问 `/admin/`。

演示命令通过作者、项目名称和帖子标题识别既有内容，不会覆盖编辑、重复添加回复或重新设置点赞。重命名演示条目后再次运行，会补回原名称的示例。演示数据是虚构内容，不代表真实项目或用户。

## 结构

- `community/models.py`：项目、主题、回复；主题通过可选外键关联项目，代码托管在外部平台。
- `community/views.py`：页面与写入操作；点赞返回 HTMX HTML 片段，禁用 JavaScript 时可正常提交表单。
- `templates/`、`static/css/site.css`：服务端页面与响应式样式。
- `locale/zh_Hans/LC_MESSAGES/`：简体中文翻译，包含已编译的 `.mo` 文件。

## 验证

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test community
```

测试集中在一个文件，覆盖发布项目和关联讨论、权限、点赞计数、搜索筛选、CSRF、Markdown 安全渲染和语言切换。

修改翻译时，安装 GNU gettext 后运行 Django 标准命令：

```bash
.venv/bin/python manage.py makemessages -l zh_Hans --ignore=.venv
.venv/bin/python manage.py compilemessages --ignore=.venv
```

## 当前运行范围

当前启动命令监听全部网卡，Django 不限制访问的 IP 和域名。正式部署需要设置 `DJANGO_DEBUG=0`、独立的 `DJANGO_SECRET_KEY`，配置 HTTPS 和静态文件服务。数据库为项目目录下的 `db.sqlite3`。

首版采用本地用户名密码认证；邮箱可选，尚未接入邮件验证、找回密码或第三方登录。项目保存外部链接，不托管代码，也不执行用户项目。

HTMX 2.0.11 的许可证保存在 `static/vendor/HTMX-LICENSE`。
