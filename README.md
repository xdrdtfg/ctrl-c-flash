# CtrlCFlash · Ctrl+C 雷霆大C

> 按下 Ctrl+C 的那一刻，在你正在复制的文字光标处炸出一个炫彩的大 **C**，然后自己消失。
> 就为了让你一眼确认——**这次复制，到底成没成**。

一个 Windows 托盘小工具，不弹窗、不打断、不占地方。复制成功与否，用眼睛看，不用猜。

<!-- 建议在仓库根目录放一张 preview.gif 或 preview.png，然后把下面这行替换掉 -->
<!-- ![preview](preview.gif) -->

---

## 它解决什么问题

复制是电脑上最高频的操作之一，但它**没有任何反馈**。
你选中一段文字、按下 Ctrl+C，屏幕上什么都没发生。于是你开始怀疑：

- 我到底选中了吗？
- 这次复制进去了吗？
- 还是刚才那个剪贴板里的旧内容？

CtrlCFlash 的答案是：在光标处炸一个彩虹大 C。看见了，就是成了。

## 特性

**外观**
- 10 套炫彩主题：彩虹流光 / 北极极光 / 霓虹果冻 / 烈焰熔岩 / 鎏金 / 冰霜 / 糖果粉 / 矩阵绿 / 赛博紫电，外加自定义双色渐变
- 渐变色会在字母上流动，流速可调（0 = 完全静止）
- 字体、字重（常规/加粗/特粗）、起始大小、最大大小、不透明度、辉光强度全部可调

**动画**
- 6 种出现方式：缩放冲入 / 旋转飞入 / 淡入浮现 / 闪烁登场 / 弹性弹跳 / 雷霆砸落
- 6 种消失方式：淡出 / 放大消散 / 缩小消失 / 旋转飞出 / 闪烁熄灭 / 上飘消散
- 出现、停留、消失三段时长可精确到毫秒；另有 轻盈 / 标准 / 夸张 三档快捷风格
- 可选的出现冲击波：一圈向外扩散的光晕

**行为**
- 优先定位到文字光标（`GetGUIThreadInfo`），拿不到就自动退回鼠标位置，不会不显示
- 中英文界面实时切换，首次运行自动跟随系统语言
- 开机自启（可选），exe 挪了位置下次会自动更新自启路径
- 全局键盘钩子 + 单实例（命名管道），不会开出第二个进程

**克制的地方**
- 无边框、置顶、点击穿透的透明浮层，不抢焦点、不挡操作
- 平时内存会自己还给系统（降到 10MB 以内），下次复制前再换回来
- 设置窗口用完就关，不在后台常驻

## 快速开始

### 方式一：直接下 exe（推荐给普通用户）

1. 到 [Releases](../../releases) 下载 `CtrlCFlash.exe`
2. 双击运行
3. 右下角托盘出现彩色 C 图标 → 随便选段文字按 `Ctrl+C`，看效果

不用安装，不用 Python，删掉 exe 就等于卸载（记得先去设置里取消「开机自动启动」）。

### 方式二：从源码跑（推荐给开发者）

```bash
git clone https://github.com/xdrdtfg/ctrl-c-flash.git
cd ctrl-c-flash
pip install -r requirements.txt
python main.py
```

要求：Windows 10/11，Python 3.9+（开发环境为 3.13）。

## 打包成单文件 exe

```bash
pip install pyinstaller
pyinstaller CtrlCFlash.spec
```

产物在 `dist/CtrlCFlash.exe`，约 25MB。

`CtrlCFlash.spec` 里做了一件事：PyInstaller 的 Qt 钩子会把整个 PySide6 都塞进来，
其中一大半是这个托盘工具永远用不到的（`opengl32sw.dll` 单个就 19.7MB、QML 全家桶、
PDF 插件、TLS 库、20 多种 Qt 自带翻译…）。spec 在 `Analysis` 之后按文件名把它们从
TOC 里摘掉，44MB → 25MB，功能和界面完全不变。具体每一项摘掉的理由都写在 spec 顶部注释里。

## 托盘操作

| 操作 | 效果 |
| --- | --- |
| 左键单击 | 预览一次动画 |
| 右键单击 | 菜单：启用/暂停 · 预览 · 设置 · 开机自启 · 退出 |
| 双击 | 打开设置窗口 |

## 配置

所有改动**即时生效**，改完直接按 Ctrl+C 就能看到，不需要点保存。

配置文件：`%APPDATA%\CtrlCFlash\config.json`（设置窗口「其它」页有一键打开按钮）。
删掉它即恢复出厂设置。

<details>
<summary>默认配置项</summary>

```json
{
  "enabled": true,
  "theme": "rainbow",
  "custom_colors": ["#FF2D75", "#00C2FF"],
  "font_family": "Microsoft YaHei",
  "font_weight": "black",
  "start_size": 46,
  "peak_size": 168,
  "opacity": 100,
  "glow": 14,
  "shockwave": false,
  "flow_speed": 1.0,
  "ui_mode": "dark",
  "language": "",
  "in_anim": "spray",
  "out_anim": "expand",
  "in_ms": 260,
  "hold_ms": 240,
  "out_ms": 460,
  "prefer_caret": true,
  "autostart": false
}
```
</details>

## 项目结构

```
main.py           入口：托盘常驻 + 单实例 + 全局按键监听
keyboard_hook.py  Win32 低级键盘钩子（WH_KEYBOARD_LL），识别 Ctrl+C
cursor_probe.py   取文字光标位置（GetGUIThreadInfo），失败回退鼠标位置
overlay.py        透明置顶浮层：渐变字母 C 的绘制与入场/停留/出场动画
themes.py         颜色主题与动画方案定义
cfg.py            配置读写 + 开机自启注册表操作
i18n.py           中英文文案表
settings_ui.py    设置窗口（三个页面）
_make_icon.py     生成 app.ico
CtrlCFlash.spec   PyInstaller 打包配置
使用说明.txt       面向普通用户的完整中文说明
```

## 已知限制

- **仅 Windows**。依赖 Win32 API（低级键盘钩子、`GetGUIThreadInfo`）和注册表自启。
- **浏览器、VS Code 这类程序不一定报告文字光标位置**。设置里关掉「优先定位到文字光标」即可改为跟随鼠标。
- **权限要对等**：在以管理员身份运行的程序里复制时，本工具也要用管理员身份启动才能收到按键。
- **部分安全软件会拦截全局键盘钩子**，需要手动加白名单。
- 触发键目前固定为 `Ctrl+C`（`Ctrl+Alt+C` 不会触发）。

更多问答见 [使用说明.txt](使用说明.txt)。

## 说明

这个工具的出发点是「复制也要有反馈」这件小事。它读键盘、画一个字母，
除此之外不联网、不上传、不记录你复制了什么——剪贴板内容它完全不碰，
只是监听那个按键组合而已。

## 许可证

[MIT](LICENSE)

---

## English

**CtrlCFlash** — visual feedback for Ctrl+C on Windows.

Press Ctrl+C and a rainbow-colored letter **C** bursts out at your text caret and fades away,
so you can *see* that the copy actually happened. A tray-resident PySide6 overlay:
click-through, always-on-top, no focus stealing, and it returns its memory to the OS when idle.

10 gradient themes, 6 in-animations × 6 out-animations, millisecond-level timing control,
caret tracking with mouse fallback, zh/en UI, optional autostart.

Download `CtrlCFlash.exe` from [Releases](../../releases), or run from source:

```bash
pip install -r requirements.txt
python main.py
```

Windows 10/11 only (uses Win32 low-level keyboard hooks). MIT licensed.
