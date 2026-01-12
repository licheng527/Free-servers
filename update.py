#!/usr/bin/env python3
"""从 Cloudflare KV 获取节点并更新 README.md"""

import os
import re
import yaml
import random
import base64
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

# 从环境变量获取配置
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_NAMESPACE_ID = os.environ.get("CF_NAMESPACE_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")
CF_KV_KEY = os.environ.get("CF_KV_KEY", "data")

def fetch_kv_data():
    """从 Cloudflare KV 获取数据"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values/{CF_KV_KEY}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def parse_nodes(yaml_content):
    """解析 YAML 中的节点"""
    data = yaml.safe_load(yaml_content)
    return data.get("proxies", [])

def node_to_link(node):
    """将节点转换为订阅链接"""
    t = node.get("type", "")
    server = node.get("server", "")
    port = node.get("port", 0)
    name = node.get("name", "")

    if t == "vmess":
        vmess_obj = {
            "v": "2", "ps": name, "add": server, "port": str(port),
            "id": node.get("uuid", ""), "aid": str(node.get("alterId", 0)),
            "net": node.get("network", "tcp"), "type": "none",
            "host": node.get("ws-opts", {}).get("headers", {}).get("Host", ""),
            "path": node.get("ws-opts", {}).get("path", ""),
            "tls": "tls" if node.get("tls") else "",
            "sni": node.get("sni") or node.get("servername", "")
        }
        return "vmess://" + base64.b64encode(json.dumps(vmess_obj).encode()).decode()

    elif t == "vless":
        params = []
        if node.get("network"): params.append(f"type={node['network']}")
        if node.get("sni") or node.get("servername"): params.append(f"sni={node.get('sni') or node.get('servername')}")
        if node.get("tls"): params.append("security=tls")
        if node.get("flow"): params.append(f"flow={node['flow']}")
        if node.get("reality-opts"):
            params.append("security=reality")
            params.append(f"pbk={node['reality-opts'].get('public-key', '')}")
            params.append(f"sid={node['reality-opts'].get('short-id', '')}")
        query = "&".join(params)
        return f"vless://{node.get('uuid', '')}@{server}:{port}?{query}#{quote(name)}"

    elif t == "ss":
        method = node.get("cipher", "aes-256-gcm")
        password = node.get("password", "")
        userinfo = base64.b64encode(f"{method}:{password}".encode()).decode()
        return f"ss://{userinfo}@{server}:{port}#{quote(name)}"

    elif t == "trojan":
        password = node.get("password", "")
        sni = node.get("sni", "")
        return f"trojan://{password}@{server}:{port}?sni={sni}#{quote(name)}"

    elif t in ("hysteria2", "hy2"):
        password = node.get("password", "")
        sni = node.get("sni") or server
        return f"hysteria2://{password}@{server}:{port}?sni={sni}#{quote(name)}"

    return ""

def update_readme(nodes):
    """更新 README.md"""
    # 随机选择3个节点
    selected = random.sample(nodes, min(3, len(nodes)))

    # 生成节点信息
    beijing_tz = timezone(timedelta(hours=8))
    update_time = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    node_lines = []
    for i, node in enumerate(selected, 1):
        link = node_to_link(node)
        if link:
            node_lines.append(f"```")
            node_lines.append(link)
            node_lines.append(f"```")
            node_lines.append("")

    # 生成 README 内容
    readme_content = f"""# Free-servers

免费节点分享，每小时自动更新

## 节点信息

更新时间：{update_time} (北京时间)

{chr(10).join(node_lines)}

## 说明

- 节点每小时自动更新
- 节点来源于网络收集
- 仅供学习交流使用

## 订阅链接

Clash 订阅：`https://jcnode.top/clash`

---

⭐ 如果觉得有用，请给个 Star！
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"README.md 已更新，包含 {len(selected)} 个节点")

def main():
    if not all([CF_ACCOUNT_ID, CF_NAMESPACE_ID, CF_API_TOKEN]):
        print("错误：缺少 Cloudflare 配置环境变量")
        return

    print("正在从 Cloudflare KV 获取数据...")
    yaml_content = fetch_kv_data()

    print("正在解析节点...")
    nodes = parse_nodes(yaml_content)
    print(f"共获取到 {len(nodes)} 个节点")

    if not nodes:
        print("没有可用节点")
        return

    update_readme(nodes)

if __name__ == "__main__":
    main()
