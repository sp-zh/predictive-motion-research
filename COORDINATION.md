# Mac 与 Dell 项目协作

更新：2026-10-07，多伦多时间。

## 实测环境

| 项目 | Mac | Dell ZH2022 |
|---|---|---|
| 当前执行环境 | macOS，Apple Silicon | Windows，WSL2 Ubuntu 24.04.4，x86_64 |
| Linux / ROS | 尚未检查 | ROS 2 Jazzy CLI 已验证 |
| CPU / 内存 | 尚未检查 | i7-12700H，14 核 20 线程，约 31.7 GiB |
| 可用磁盘 | 当前约 29 GiB；初始约 43 GiB | C 初始约 199.6 GiB；D 当前约 476 GiB |
| 数据线地址 | bridge0：169.254.142.85 | USB4 网卡：169.254.118.3 |

Mac USB4 总线报告 40 Gb/s；Dell USB4 网络接口报告 20 Gb/s。两端网络、SSH 公钥登录、双向 256 MiB 文件传输及中断续传均已验证。链路本地地址可能变化，每次启动前重新检查。

## 分工

项目 prompt 已接收，Phase 0–4 组件审查已通过；用户已恢复项目，Phase 5 正在开发，尚未通过独立根验收。Mac 管理需求、独立审查、代码整合和 macOS 专属工作；Dell WSL 承担适合 Ubuntu 24.04 / ROS 2 Jazzy 的构建、测试和批处理。ROS1、其他 ROS 发行版、GPU、硬件直通及实时控制能力尚未验证，按具体项目补齐。

Linux 编译工作区优先放 WSL 原生文件系统；大型原始数据优先放 D 盘。WSL 虚拟盘显示的可用容量不能当作额外物理磁盘容量。不同平台分别保存构建产物，共享源码、输入数据、校验清单和结果。

Dell 原协作聊天：`01a0a7f2-cc0b-77d0-8ed7-15abe948879a`（检查接电时自动休眠问题）。远程 host：`remote-control:env_e_6aa97971e7c8832ca5cdcb0ff2bcef3b`。2026-10-07 用户在「将 ROS 项目文件存入 WSL」批准保存交接文件并切换干净聊天。旧聊天已在训练采集完成、无运行中实验/构建时释放开发写入，不再向其追加开发任务。

新协作聊天：`01a114d9-3a3a-7071-b94f-624581000992`（Phase5：通过数据线继续 Dell 项目），hostId=`local`。新聊天运行在 Mac，通过现有 USB4 SSH 操作同一个 Dell WSL 项目，不复制或初始化项目。已核对原始用户交接授权、旧写入者释放状态和归档；新聊天在 Dell 的 `PHASE5_WRITER_STATE_20261007.json` 登记唯一开发写入，Mac 根只做独立审查和统一 Git 备份。原 WSL 项目和大型 D 盘证据保持原位置。旧状态文件与历史交接快照保留。

## 当前传输状态

备用 SMB 共享：`smb://169.254.118.3/CableTransfer`，映射到 Dell 的 `C:\Users\SYSUR\Documents\Codex\CableTransfer`。权限为 `ZH2022\sp` 可修改。Mac 自动挂载因缺少认证失败，目前没有挂载，SMB 通道没有传输实测。当前使用已验证的 USB4 地址 SSH 通道。

Dell 已创建 `C:\Users\SYSUR\Documents\Codex\2026-09-16\zh\CodexTransfer\inbox`、`outbox`、`manifests`，该目录没有新增共享。当前主要传输目录已配置为 D:\CodexTransfer，下述 SMB 路径仅作备用。

可先在 Finder 的“前往 → 连接服务器”登录现有共享。密码由用户在系统登录框中输入，不写进脚本或聊天。挂载成功后，使用已核实的实际挂载路径运行：

```sh
/opt/homebrew/bin/python3 /Users/uot/Documents/ChatGPT/ros/tools/transfer.py /absolute/source /Volumes/CableTransfer --manifest /Users/uot/Documents/ChatGPT/ros/transfer/manifests/upload.json
```

下载时交换来源和目标；目标目录需预先存在。脚本复制普通文件或目录中的普通文件，保留中断后的 `.codex-part` 文件；重新运行同一命令时先校验已有前缀再续传，完成后对目标做 SHA-256 校验并生成清单。默认至少保留 10 GiB 空间。不删除来源，也不覆盖内容不同的已存在文件。复制期间保持来源不变，并且不要对同一个目标并发运行。目录中的符号链接和特殊文件需要按项目单独处理；空目录不会复制。

## 已验证的 SSH 传输通道

用户在 Dell 聊天直接批准后，安装配置已完成。OpenSSH 专用服务和 WSL 保活进程正在运行，账户 codextransfer 无 sudo，仅接受 Mac 公钥；密码、root 登录和 SSH 转发禁用。Windows 仅在 169.254.118.3:2222 转发到 WSL，防火墙只允许 Mac 169.254.142.85。数据位于 D:\CodexTransfer，对应 /mnt/d/CodexTransfer，含 inbox/outbox/manifests。

服务器 ED25519 指纹已从 Dell 端取得并在 Mac 固定核验：SHA256:YeWtFYApPg3CNAiMhEz+YFGysfAr82PX3VxKseU1DBU。

Dell 安装、启动、停止与回滚脚本位于 C:\Users\SYSUR\Documents\Codex\2026-09-16\zh\outputs\transfer-setup\：Install.ps1、install-linux.sh、Prepare.ps1、Stop.ps1、Rollback.ps1。Windows/WSL 重启后应由 Dell 协作聊天执行 Prepare.ps1 刷新动态 WSL 地址。链路本地地址变化时需重新核实接口及更新限定地址规则，不放宽到其他网络。回滚保留数据与已安装的软件包。

实际测试：256 MiB 随机文件，上传过程中主动中断并保留 16,744,448 字节，续传日志证实复用全部已有内容；上传和下载 SHA-256 均一致。上传续传含检查及哈希耗时 10.41 秒，下载含检查及哈希耗时 5.73 秒。传输阶段日志约上传 32–55 MB/s、下载 73–104 MB/s；该结果不是 20/40 Gb/s 链路带宽上限，长期稳定性和更大规模吞吐尚未测试。结果和哈希清单保存在 transfer/manifests/。

NTFS/DrvFS 拒绝专用账号修改 POSIX 时间戳，因此同步工具不修改权限、所有者或时间戳，使用内容校验判断文件差异。代码构建仍优先使用 WSL 原生文件系统。

Mac 专用密钥已生成，私钥仅存于被 Git 忽略的 `.transfer-private/`，权限受限；公钥已配置到 Dell 专用账户。不得提交或传输私钥。

Mac SSH 配置已写入 `.transfer-private/ssh_config`，要求固定主机密钥；服务器公钥已写入 `known_hosts`，不使用跳过主机验证的选项。SSH 连接工具是 `tools/dell-ssh.sh`。SSH 通道及以下同步工具已通过真实两端验证：

```sh
# 上传目录内容到 Dell D 盘 inbox/dataset
/opt/homebrew/bin/python3 /Users/uot/Documents/ChatGPT/ros/tools/dell-sync.py push /absolute/local/dataset dataset
# 下载 Dell D 盘 outbox/results 到 Mac 本地目录
/opt/homebrew/bin/python3 /Users/uot/Documents/ChatGPT/ros/tools/dell-sync.py pull /absolute/local/results results
```

该同步工具使用 rsync 保留 `.rsync-partial`，成功后比对两端 SHA-256 并保存清单。默认保留 10 GiB 空间，容量预检按整个数据集大小保守计算，不自动删除目标中的额外文件。传输期间输入数据必须保持不变。服务器核验、双向文件传输、中断续传和 SHA-256 测试均通过，当前可以使用。

项目证据包必须先写 `.part`，完成压缩后计算哈希并原子重命名，最后发布 `READY`。接收端等到 `READY` 后才开始拉取和核验。Phase 3 曾在压缩过程中提前拉取，哈希校验拒绝该未完成文件；按此协议重新发布后，516,910,135 字节证据包通过完整校验。大型后续原始数据保留 Dell D 盘，只将源码、审查、汇总和选定图表传回 Mac。

官方参考：[WSL 网络与端口转发](https://learn.microsoft.com/en-us/windows/wsl/networking)、[Ubuntu OpenSSH 服务](https://ubuntu.com/server/docs/how-to/security/openssh-server/)。
