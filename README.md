# 环境搭建指南

本指南帮助你在**任何一台新电脑**（Linux / Windows / macOS）上完成 AI for Protein Design 实验环境的搭建。

---

## 0. 连接 VPN

本项目的代码和模型权重托管在 GitHub 和 Facebook Research，国内网络可能无法直接访问。请先连接 VPN。

推荐使用 **GsouCloud**（注册即送免费流量）：

1. 访问 <https://www.gsoucloud.com> 注册账号
2. 下载对应系统的客户端并安装
3. 选择**美国节点**连接
4. 确认连接成功后继续下一步

---

## 1. 打开终端

终端（Terminal）是输入命令的地方。不同系统打开方式不同：

- **Ubuntu / Debian**：按 `Ctrl+Alt+T`
- **其他 Linux**：在应用菜单搜索 `Terminal` 或 `终端`
- **macOS**：按 `Cmd+Space`，输入 `Terminal` 回车
- **Windows**：按 `Win+R`，输入 `cmd` 回车。或用 `Win+R` 输入 `powershell` 打开 PowerShell。

打开后你会看到一个黑色（或白色）的窗口，里面有一行提示符，比如 `user@hostname:~$`。这就是你输入命令的地方。

> **重要提示**：在终端里，`Ctrl+C` 不是复制——它会**终止当前正在运行的程序**（比如正在下载的文件会中断且消失）。复制粘贴请用：
> 
> - **复制**：`Ctrl+Shift+C`
> - **粘贴**：`Ctrl+Shift+V`

---

## 2. 安装 Node.js 和 npm

先检查是否已经安装。在终端输入：

```bash
node --version
```

如果显示版本号（如 `v22.x.x`），跳过这一步。如果提示 `command not found`，按你的系统选择安装方式：

#### Linux / macOS

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
```

安装完成后，**关闭当前终端窗口，重新打开一个新终端**，然后输入：

```bash
nvm install 24
```

#### Windows

Windows 不支持 nvm-sh。请使用 **nvm-windows**：

1. 访问 <https://github.com/coreybutler/nvm-windows/releases>
2. 下载最新版 `nvm-setup.exe` 并安装
3. 打开新的 cmd 窗口，输入：

```cmd
nvm install 24
nvm use 24
```

或者直接下载 Node.js 安装包：访问 <https://nodejs.org>，下载 LTS 版本（v24.x.x）的 `.msi` 安装程序，双击安装即可。

---

验证安装成功：

```bash
node --version   # 应显示 v24.x.x
npm --version    # 应显示 10.x.x 或更高
```

---

## 3. 安装 OpenCode

在终端输入：

```bash
npm install -g opencode-ai@latest
```

验证安装成功：

```bash
opencode --version
```

---

## 4. 准备项目文件夹

```bash
mkdir -p ~/protein_learn
cd ~/protein_learn
```

---

## 5. 放入 AGENTS.md

把本仓库的 `AGENTS.md` 复制到项目文件夹：

```bash
cp AGENTS.md ~/protein_learn/
```

> 如果你是从 GitHub 克隆的仓库，`AGENTS.md` 就在仓库根目录。如果你是通过其他方式获得的，请把 `AGENTS.md` 放在 `~/protein_learn/` 下。

---

## 6. 启动 OpenCode

确保你在项目文件夹中：

```bash
cd ~/protein_learn
opencode
```

启动后你会进入 OpenCode 的交互界面。输入以下内容告诉 AI 你的需求：

```
请协助我从头配置好环境
```

AI 会读取 `AGENTS.md`，按照步骤引导你：

1. 安装 SSH 远程控制插件
2. 创建 AutoDL 云主机
3. 配置 SSH 密钥免密登录
4. 自动化部署 ProteinMPNN、RFDiffusion、ESMFold

你只需要按提示操作即可，不需要记住任何命令。
