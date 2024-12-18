# 小米/红米路由器 SSH 开启工具

一个用于自动化获取小米/红米路由器 SSH 访问权限的 Python 工具。

## 路由器环境要求
- 小米万兆路由器: MiWiFi ROM 稳定版 1.0.53
- 小米路由器 AC2100: MiWiFi ROM 稳定版 2.0.743
- 小米路由器 AX1800: MiWiFi ROM 稳定版 1.0.399
- 小米路由器 AX3000: MiWiFi ROM 稳定版 1.0.48 / 1.0.46
- 小米 AIoT 物联路由器 AX3600: MiWiFi ROM 稳定版 1.1.21
- 小米路由器 AX9000: MiWiFi ROM 稳定版 1.0.165
- 小米 AIoT 物联路由器 AC2350: MiWiFi ROM 稳定版 1.3.8
- 红米路由器 AX5400 电竞版: MiWiFi ROM 稳定版 1.0.95
- 红米路由器 AX3000: MiWiFi ROM 稳定版 1.0.33
- 其他没注明的路由器可以测试是否能开启
- 本人路由器红米 ax1800 可以正常开启



## 功能特点

- 支持小米/红米路由器系列
- 已在红米 AX1800 上实践验证
- 自动检测路由器是否支持开启 SSH
- 全自动化配置过程
- 提供详细的操作指南

## 使用前提

1. Python 3.x 环境
2. 路由器已连接并可访问管理界面
3. 已登录路由器管理后台

## 安装依赖



## 使用说明

1. 登录路由器管理后台 (http://192.168.31.1)
2. 复制浏览器地址栏的完整链接
3. 运行脚本并按提示操作：


## 自动化流程

工具会自动完成以下操作：
- 设置系统时间
- 解锁 SSH 访问
- 提供连接 SSH 指南
- 恢复路由器原始时间

## 注意事项

1. 操作前请确保路由器固件版本合适
2. 建议先备份路由器配置
3. 操作过程中请勿断开电源
4. 如遇问题可重启路由器重试

## 常见问题

如遇到问题，请访问以下链接查看解决方案：
https://www.right.com.cn/forum/thread-8348455-1-1.html

## 致谢

原创作者: Minorice  
原帖地址: https://www.right.com.cn/forum/thread-8348455-1-1.html

## 免责声明

本工具仅供学习研究使用，使用本工具可能会导致路由器保修失效。使用者需自行承担使用本工具的风险。

## License

MIT License


