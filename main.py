#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
###############################################################################
#                                                                             
#                         小米路由器 SSH 连接工具                              
#                     Xiaomi Router SSH Connection Tool                        
#                                                                             
###############################################################################

功能说明:
---------
本脚本用于自动化获取小米路由器的 SSH 访问权限，包含以下步骤：
1. 设置系统时间
2. 解锁 dropbear 配置
3. 激活 SSH 配置
4. 启动 dropbear 服务
5. 建立 SSH 连接并同步时间

使用方法:
---------
1. 安装依赖：pip install requests paramiko
2. 设置路由器IP和Token
3. 运行脚本：python router_hack.py

作者: [你的名字]
版本: 1.0.0
日期: 2024-03-xx
"""

# 只导入基本模块
import sys
import subprocess
from importlib import import_module

def install_dependencies():
    """
    检查并安装必要的依赖包
    """
    try:
        from importlib.metadata import distributions
        required = {'requests', 'paramiko'}
        installed = {dist.metadata['Name'] for dist in distributions()}
        missing = required - installed

        if missing:
            print("\n=== 检测到缺少必要依赖包 ===")
            print("需要安装以下包:")
            for pkg in missing:
                print(f"- {pkg}")
            
            response = input("\n是否现在安装? [Y/n]: ").lower() or 'y'
            if response == 'y':
                print("\n正在安装依赖包...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
                print("依赖包安装完成！\n")
                return True
            else:
                print("\n警告: 缺少必要依赖包，程序可能无法正常运行！")
                return False
        return True
    except Exception as e:
        print(f"安装依赖包时出错: {str(e)}")
        return False

def extract_host_token(url):
    """
    从小米路由器后台链接中提取 host 和 token
    例如：http://192.168.31.1/cgi-bin/luci/;stok=504081039f4aef9b51d1c9bdae300539/web/home#router
    """
    import re
    try:
        # 提取 host
        host_match = re.search(r'http://([^/]+)', url)
        host = host_match.group(1) if host_match else None
        
        # 提取 stok
        token_match = re.search(r'stok=([^/]+)', url)
        token = token_match.group(1) if token_match else None
        
        return host, token
    except Exception:
        return None, None

class RouterHack:
    def __init__(self, host, token):
        """
        初始化路由器操作类
        :param host: 路由器IP地址
        :param token: 路由器stok令牌
        """
        # 导入必要的模块
        import requests
        import json
        import time  # 在类中导入time模块
        from datetime import datetime  # 添加 datetime 导入
        
        self.requests = requests
        self.json = json
        self.time = time  # 保存time模块引用
        self.datetime = datetime  # 保存 datetime 引用
        
        self.host = host
        self.token = token
        self.base_url = f"http://{host}/cgi-bin/luci/;stok={token}"

    def set_system_time(self):
        """
        第2步: 设置系统时间
        """
        try:
            # 获取当前时间并格式化
            current_time = self.datetime.now()
            formatted_time = current_time.strftime("%Y-%-m-%-d%%20%-H:%-M:%-S")  # 修改格式化方式，去掉前导零
            
            # 构建URL
            url = f"{self.base_url}/api/misystem/set_sys_time?time={formatted_time}&timezone=CST-8"
            
            print("步骤 2.1: 发送系统时间设置请求...")
            response = self.requests.get(url)
            result = response.json()
            print(f"响应数据: {self.json.dumps(result, ensure_ascii=False, separators=(',', ':'))}")
            
            if result.get('code') == 0:
                print("操作成功")
                self.time.sleep(3)
                return True
            else:
                print(f"请求错误: {result.get('msg', '未知错误')}")
                # print("❌ 检测到错误，终止操作")
                return False

        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")
            return False

    def unlock_dropbear(self):
        """
        第3步: 解锁dropbear配置
        
        功能说明:
        1. 通过注入漏洞在路由器上以 root 身份执行命令
        2. 使用 sed 命令将 /etc/init.d/dropbear 中的所有 release 替换为 XXXXXX
        3. 这个步骤是为了绕过系统对 dropbear 服务的限制
        """
        try:           
            url = f"{self.base_url}/api/xqsmarthome/request_smartcontroller"

            # 步骤 3.1: 发送解锁请求
            print("步骤 3.1: 发送解锁请求...")
            payload_data1 = {
                "command": "scene_setting",
                "name": "'$(sed -i s/release/XXXXXX/g /etc/init.d/dropbear)'",  # 使用 sed 替换命令
                "action_list": [{
                    "thirdParty": "xmrouter",
                    "delay": 17,
                    "type": "wan_block",
                    "payload": {
                        "command": "wan_block",
                        "mac": "00:00:00:00:00:00"
                    }
                }],
                "launch": {
                    "timer": {
                        "time": "3:1",
                        "repeat": "0",
                        "enabled": True
                    }
                }
            }
            
            response1 = self.requests.post(url, data={"payload": self.json.dumps(payload_data1)})
            result1 = response1.json()
            print(f"响应数据: {self.json.dumps(result1, ensure_ascii=False, separators=(',', ':'))}")
            
            # 详细的错误判断
            if result1.get('code') == 0:
                print("操作成功")
            elif result1.get('code') == 3001:
                print("\n❌ stok 代币值已过期")
                print("请重新登录 Web 管理后台获取新的 stok 值")
                print("\n❌ 检测到错误，终止操作")
                return False
            elif result1.get('code') == -101:
                print("\n❌ 连接到小米智能场景控制器服务 smartcontroller.service 失败")
                print("建议尝试以下操作：")
                print("1. 重启路由器")
                print("2. 恢复出厂设置")
                print("\n❌ 检测到错误，终止操作")
                return False
            else:
                print(f"请求错误: {result1.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)
            
            # 步骤 3.2: 启动场景
            print("步骤 3.2: 启动场景...")
            payload_data2 = {
                "command": "scene_start_by_crontab",
                "time": "3:1",
                "week": 0
            }
            
            response2 = self.requests.post(url, data={"payload": self.json.dumps(payload_data2)})
            result2 = response2.json()
            print(f"响应数据: {self.json.dumps(result2, ensure_ascii=False, separators=(',', ':'))}")
            if result2.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result2.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)
            
            # 最终结果判断
            print()
            print("##解锁dropbear配置 操作全部完成")
            return True

        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            return False

    def activate_ssh(self):
        """
        第4步: 使用 nvram 激活 ssh_en 配置项
        """
        try:
            url = f"{self.base_url}/api/xqsmarthome/request_smartcontroller"

            # 步骤 4.1: 设置 ssh_en=1
            print("步骤 4.1: 设置 ssh_en=1...")
            payload_data1 = {
                "command": "scene_setting",
                "name": "'$(nvram set ssh_en=1)'",
                "action_list": [{
                    "thirdParty": "xmrouter",
                    "delay": 17,
                    "type": "wan_block",
                    "payload": {
                        "command": "wan_block",
                        "mac": "00:00:00:00:00:00"
                    }
                }],
                "launch": {
                    "timer": {
                        "time": "3:2",
                        "repeat": "0",
                        "enabled": True
                    }
                }
            }
            
            response1 = self.requests.post(url, data={"payload": self.json.dumps(payload_data1)})
            result1 = response1.json()
            print(f"响应数据: {self.json.dumps(result1, ensure_ascii=False, separators=(',', ':'))}")
            if result1.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result1.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)
            
            # 步骤 4.2: 启动第一个场景
            print("步骤 4.2: 启动场景...")
            payload_data2 = {
                "command": "scene_start_by_crontab",
                "time": "3:2",
                "week": 0
            }
            response2 = self.requests.post(url, data={"payload": self.json.dumps(payload_data2)})
            result2 = response2.json()
            print(f"响应数据: {self.json.dumps(result2, ensure_ascii=False, separators=(',', ':'))}")
            if result2.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result2.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)

            # 步骤 4.3: 执行 nvram commit
            print("步骤 4.3: 执行 nvram commit...")
            payload_data3 = {
                "command": "scene_setting",
                "name": "'$(nvram commit)'",
                "action_list": [{
                    "thirdParty": "xmrouter",
                    "delay": 17,
                    "type": "wan_block",
                    "payload": {
                        "command": "wan_block",
                        "mac": "00:00:00:00:00:00"
                    }
                }],
                "launch": {
                    "timer": {
                        "time": "3:3",
                        "repeat": "0",
                        "enabled": True
                    }
                }
            }
            response3 = self.requests.post(url, data={"payload": self.json.dumps(payload_data3)})
            result3 = response3.json()
            print(f"响应数据: {self.json.dumps(result3, ensure_ascii=False, separators=(',', ':'))}")
            if result3.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result3.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)

            # 步骤 4.4: 启动第二个场景
            print("步骤 4.4: 启动第二个场景...")
            payload_data4 = {
                "command": "scene_start_by_crontab",
                "time": "3:3",
                "week": 0
            }
            response4 = self.requests.post(url, data={"payload": self.json.dumps(payload_data4)})
            result4 = response4.json()
            print(f"响应数据: {self.json.dumps(result4, ensure_ascii=False, separators=(',', ':'))}")
            if result4.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result4.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)

            # 步骤 4.5: 检查SSH支持
            print("步骤 4.5: 检查路由器SSH支持...")
            check_url = f"{self.base_url}/api/xqsystem/fac_info"
            response = self.requests.get(check_url)
            result = response.json()
            print(f"响应数据: {self.json.dumps(result, ensure_ascii=False, separators=(',', ':'))}")

            # 检查响应中的 ssh 值
            if result.get('ssh') == True:  # 明确检查 ssh 值是否为 True
                print("✓  恭喜，检测到路由器支持开启SSH功能")
                self.time.sleep(5)
                print("\n##使用 nvram 激活 ssh_en 配置项 操作全部完成")
                return True
            else:
                print("\n❌ 太可惜了，此路由器当前ROM不支持开启SSH")
                print("检测到 ssh 值为 false")
                print("建议更新路由器固件后重试")
                print("\n❌ 检测到错误，终止操作")
                return False

        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            return False

    def start_dropbear(self):
        """
        第5步: 启动 dropbear 服务
        """
        try:

            url = f"{self.base_url}/api/xqsmarthome/request_smartcontroller"

            # 步骤 5.1: 启用 dropbear
            print("步骤 5.1: 启用 dropbear...")
            payload_data1 = {
                "command": "scene_setting",
                "name": "'$(/etc/init.d/dropbear enable)'",  # 启用 dropbear
                "action_list": [{
                    "thirdParty": "xmrouter",
                    "delay": 17,
                    "type": "wan_block",
                    "payload": {
                        "command": "wan_block",
                        "mac": "00:00:00:00:00:00"
                    }
                }],
                "launch": {
                    "timer": {
                        "time": "3:4",  # 时间设置为 3:4
                        "repeat": "0",
                        "enabled": True
                    }
                }
            }
            
            response1 = self.requests.post(url, data={"payload": self.json.dumps(payload_data1)})
            # print("步骤 5.1 请��结果 ===")
            result1 = response1.json()
            print(f"响应数据: {self.json.dumps(result1, ensure_ascii=False, separators=(',', ':'))}")
            if result1.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result1.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)
            
            # 步骤 5.2: 启动第一个场景
            print("步骤 5.2: 启动场景...")
            payload_data2 = {
                "command": "scene_start_by_crontab",
                "time": "3:4",  # 与上一步时间一致
                "week": 0
            }
            response2 = self.requests.post(url, data={"payload": self.json.dumps(payload_data2)})
            # print("步骤 5.2 请求结果 ===")
            result2 = response2.json()
            print(f"响应数据: {self.json.dumps(result2, ensure_ascii=False, separators=(',', ':'))}")
            if result2.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result2.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)

            # 步骤 5.3: 重启 dropbear
            print("步骤 5.3: 重启 dropbear...")
            payload_data3 = {
                "command": "scene_setting",
                "name": "'$(/etc/init.d/dropbear restart)'",  # 重启 dropbear
                "action_list": [{
                    "thirdParty": "xmrouter",
                    "delay": 17,
                    "type": "wan_block",
                    "payload": {
                        "command": "wan_block",
                        "mac": "00:00:00:00:00:00"
                    }
                }],
                "launch": {
                    "timer": {
                        "time": "3:5",  # 时间变更为 3:5
                        "repeat": "0",
                        "enabled": True
                    }
                }
            }
            response3 = self.requests.post(url, data={"payload": self.json.dumps(payload_data3)})
            # print("步骤 5.3 请求结果 ===")
            result3 = response3.json()
            print(f"响应数据: {self.json.dumps(result3, ensure_ascii=False, separators=(',', ':'))}")
            if result3.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result3.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)

            # 步骤 5.4: 启动第二个场景
            print("步骤 5.4: 启动第二个场景...")
            payload_data4 = {
                "command": "scene_start_by_crontab",
                "time": "3:5",  # 与上一步时间一致
                "week": 0
            }
            response4 = self.requests.post(url, data={"payload": self.json.dumps(payload_data4)})
            # print("步骤 5.4 请求结果 ===")
            result4 = response4.json()
            print(f"响应数据: {self.json.dumps(result4, ensure_ascii=False, separators=(',', ':'))}")
            if result4.get('code') == 0:
                print("操作成功")
            else:
                print(f"请求错误: {result4.get('msg', '未知错误')}")
                print("\n❌ 检测到错误，终止操作")
                return False
            self.time.sleep(3)

            # 最终结果判断
            print()
            print("##启动 dropbear 服务 操作全部完成")
            return True

        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            return False

    def show_ssh_tips(self):
        """
        显示SSH连接提示信息
        """
        print("\n=== SSH 连接说明 ===")
        print("1. 通过（S/N码）获取SSH密码:")
        print("   → 访问 https://miwifi.dev/ssh")
        print("   → 输入路由器后台主页中的S/N码进行获取密码")
        print("   → 获取的密码即为SSH登录密码")
        
        print("\n2. 使用以下命令连接路由器:")
        print(f"   ssh root@{self.host}")
        print("   如果无法登录考虑实用:")
        print(f"   ssh -oHostKeyAlgorithms=+ssh-rsa root@{self.host}")
        


    def show_ssh_guide(self):
        """
        第6步: SSH连接说明
        """
        try:
            print("\n第6步: SSH连接说明")
            print("-" * 40)

            # 显示SSH连接提示
            self.show_ssh_tips()
            
            # 用户交互
            print("\n→ 仔细阅读信息，回车键进行下一步...")
            input()
            return True

        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            return False

    def reset_system_time(self):
        """
        第7步: 重置路由器时间为当前时间
        """
        try:
            print("\n第7步: 重置路由器时间")
            print("-" * 40)
            self.time.sleep(2)

            # 获取当前时间并格式化
            current_time = self.datetime.now()
            formatted_time = current_time.strftime("%Y-%-m-%-d%%20%-H:%-M:%-S")
            
            # 构建URL
            url = f"{self.base_url}/api/misystem/set_sys_time?time={formatted_time}&timezone=CST-8"
            
            print("步骤 7.1: 发送时间重置请求...")
            response = self.requests.get(url)
            result = response.json()
            print(f"响应数据: {self.json.dumps(result, ensure_ascii=False, separators=(',', ':'))}")
            
            if result.get('code') == 0:
                print("✓ 时间重置成功")
                print(f"当前时间已设置为: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.time.sleep(2)
                return True
            else:
                print(f"\n❌ 时间重置失败: {result.get('msg', '未知错误')}")
                return False

        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            return False

    def show_hardening_notice(self):
        """
        第8步: 显示硬固化提示信息
        """
        try:
            print("\n第8步: SSH硬固化说明")
            print("-" * 40)
            self.time.sleep(2)

            print("\n[!] 重要提示")
            print("1. 路由器重启后，SSH访问权限会丢失")
            print("2. 如需保持SSH永久访问，需要进行硬固化操作")
            print("\n[!] 风险警告")
            print("1. 硬固化操作具有一定风险")
            print("2. 本程序目前不提供硬固化操作")
            
            print("\n" + "=" * 50)
            print("程序执行完成!")
            print("感谢原作者 Minorice 的开源贡献")
            print("=" * 50)
            
            # 用户交互
            print("\n→ 按回车键结束程序...")
            input()
            
            return True

        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            return False

def show_welcome_banner():
    """
    显示欢迎界面并等待用户确认
    """
    banner = """
╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
│                                                  │
│             小米路由器 SSH 连接工具              │
│         XiaoMi Router SSH Connection Tool        │
│                                                  │
│            版本: 1.0.0  作者: WangDao            │
│                                                  │
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
    """
    print(banner)
    print("\n功能说明:")
    print("-" * 50)
    print("本工具用于自动化获取小米/红米路由器的 SSH 访问权限")
    print("原创作者: Minorice")
    print("原帖地址: https://www.right.com.cn/forum/thread-8348455-1-1.html")
    print("\n支持功能：")
    print("1. 支持小米/红米路由器")
    print("2. 已经在红米AX1800 上实践使用")
    print("3. 路由器是否支持开启 ssh会有提示")
    print("4. 个别路由器需要特定 rom 版本")
    print("-" * 50)
    
    print("\n使用说明:")
    print("-" * 50)
    print("1. 需要先登录路由器管理后台")
    print("2. 复制浏览器地址栏完整链接")
    print("3. 工具会自动完成以下操作：")
    print("   → 设置系统时间")
    print("   → 解锁 SSH 访问")
    print("   → 提供连接ssh指南")
    print("   → 恢复路由器原始时间")
    print("-" * 50)
    
    print("\n注意事项:")
    print("-" * 50)
    print("1. 操作前请确保路由器固件版本合适")
    print("2. 建议先备份路由器配置")
    print("3. 操作过程中请勿断开电源")
    print("4. 如遇问题可重启路由器重试")
    print("-" * 50)
    
    # 用户确认
    while True:
        choice = input("确认好进行操作[Y/n]: ").lower()
        if choice == 'n':
            print("\n已取消操作，程序退出...")
            sys.exit(0)
        elif choice == 'y' or choice == '':
            print("用户已确认，开始执行...")
            return True
        else:
            print("无效的输入，请输入 Y 或 n")

def main():
    """
    主函数 - 按引导步骤执行
    """
    # 显示欢迎界面并等待用户确认
    if not show_welcome_banner():
        return
    
    # 首先检查并安装依赖
    if not install_dependencies():
        return
    
    # 在依赖安装完成后再导入所需模块
    try:
        import requests
        import paramiko
        import time
        from datetime import datetime
    except ImportError as e:
        print(f"导入模块失败: {str(e)}")
        return

    print("\n开始执行自动化配置流程...")
    
    # 第一步：获取路由器信息
    print("\n第1步: 配置路由器信息")
    print("-" * 40)
    print("请按照以下步骤操作：")
    print("1. 登录小米路由器后台http://192.168.31.1")
    print("2. 保持登录状态")
    print("3. 复制浏览器地址栏的完整链接")
    print("示例链接：http://192.168.31.1/cgi-bin/luci/;stok=xxxxxx/web/home#router")
    
    # 设置默认链接
    # default_url = "http://192.168.31.1/cgi-bin/luci/;stok=e3e0eb8b0e655cac89972d7428ddae75/web/home#router"
    
    while True:
        url = input(f"请输入链接: ").strip()
        host, token = extract_host_token(url)
        
        if host and token:
            print(f"已成功提取信息:")
            print(f"#路由器IP: {host}#Token: {token}")
            
            while True:
                confirm = input("信息确认正确? [Y/n]: ").lower()
                if confirm == 'y' or confirm == '':
                    break
                elif confirm == 'n':
                    break
                else:
                    print("请输入 Y 或 N")
            
            if confirm == 'y' or confirm == '':
                break
        else:
            print("\n错误: 无法从链接中提取必要信息！")
            print("请确保复制了完整的链接地址")
            retry = input("是否重新输入? [Y/n]: ").lower() or 'y'
            if retry != 'y':
                return

    # 创建RouterHack实例
    router = RouterHack(host, token)
    
    # 执行配置步骤
    steps = [
        ("设置系统时间", router.set_system_time),
        ("解锁dropbear配置", router.unlock_dropbear),
        ("激活SSH", router.activate_ssh),
        ("启动dropbear服务", router.start_dropbear)
    ]
    
    # 按顺序执行步骤
    for i, (step_name, step_func) in enumerate(steps, 2):
        print(f"\n第{i}步: {step_name}")
        print("-" * 40)
        
        if step_func():
            print(f"✓ {step_name}执行成功")
        else:
            print(f"✗ {step_name}执行失败")
            print("\n配置过程已终止")
            print("\n获取帮助：")
            print("-" * 40)
            print("1. 请访问以下链接查看常见问题与解决方案：")
            print("   https://www.right.com.cn/forum/thread-8348455-1-1.html")
            print("2. 在页面中搜索遇到的错误信息")
            print("3. 如果问题仍未解决，可以在帖子中留言求助")
            print("-" * 40)
            return

    # 第6步: 显示SSH连接说明
    if not router.show_ssh_guide():
        return
            
    # 第7步: 重置路由器时间
    if not router.reset_system_time():
        return
            
    # 第8步: 显示硬固化提示
    router.show_hardening_notice()

if __name__ == "__main__":
    main()