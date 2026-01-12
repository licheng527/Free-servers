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

    node_links = []
    for node in selected:
        link = node_to_link(node)
        if link:
            node_links.append(link)

    # 生成 README 内容
    readme_content = f"""<h2>点击加入 Telegram 电报频道：</h2>
<blockquote>
<p style="text-align: center;"><a href="https://t.me/jcnode">https://t.me/jcnode</a></p>
</blockquote>

<h2>免费节点：</h2>
<blockquote>
<p style="text-align: center;">节点每小时自动更新，更新时间：{update_time} (北京时间)</p>
</blockquote>
<h4>本页面由某人实时手动挨个节点测速，但不同地区运营商网络仍有差异，可能会有超时节点。</h4>
<blockquote>
<p style="text-align: center;">测节点->吃饭->睡觉。</p>
</blockquote>

<h4>节点列表：(这里仅展示部分节点)</h4>

```
{chr(10).join(node_links)}
```

---

# 常用软件工具下载

## Windows 版本下载

| 客户端 | 官方下载链接 |
|:------:|:------------:|
| Karing | [下载](https://github.com/KaringX/karing/releases) |
| FLClash | [下载](https://github.com/chen08209/FlClash/releases) |
| Clash Verge | [下载](https://github.com/clash-verge-rev/clash-verge-rev/releases) |
| clash-party | [下载](https://github.com/mihomo-party-org/clash-party/releases) |
| sparkle | [下载](https://github.com/xishang0128/sparkle/releases) |
| Clash Mi | [下载](https://github.com/KaringX/clashmi/releases) |

## Android 版本下载

| 客户端 | 官方下载链接 |
|:------:|:------------:|
| Karing | [下载](https://github.com/KaringX/karing/releases) |
| FLClash | [下载](https://github.com/chen08209/FlClash/releases) |
| ClashMetaForAndroid | [下载](https://github.com/MetaCubeX/ClashMetaForAndroid/releases) |
| Hiddify | [下载](https://github.com/hiddify/hiddify-app/releases) |
| NekoBox | [下载](https://github.com/MatsuriDayo/NekoBoxForAndroid) |
| Sing-box | [下载](https://github.com/SagerNet/sing-box/releases) |
| Clash Mi | [下载](https://github.com/KaringX/clashmi/releases) |

## iOS 版本下载

| 客户端 | 官方下载链接 | 备注 |
|:------:|:------------:|:----:|
| Clash Mi | [下载](https://apps.apple.com/us/app/clash-mi/id6744321968) | 免费 |
| Sing-box VT | [下载](https://apps.apple.com/us/app/sing-box-vt/id6673731168) | 免费 |
| Hiddify | [下载](https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532) | 免费 |
| Karing | [下载](https://apps.apple.com/us/app/karing/id6472431552) | 免费 |
| Shadowrocket | [下载](https://apps.apple.com/us/app/shadowrocket/id932747118) | 付费，[公益共享账号1](https://id.jincaii.com/) [公益共享账号2](https://free.iosapp.icu/) [公益共享账号3](https://idfree.top/) [公益共享账号4](https://ios.juzixp.com/) |
| Stash | [下载](https://apps.apple.com/us/app/stash-rule-based-proxy/id1596063349) | 付费 |
| Loon | [下载](https://apps.apple.com/us/app/loon/id1373567447) | 付费 |
| Surge | [下载](https://apps.apple.com/us/app/surge-5/id1442620678) | 付费 |

## MacOS 版本下载

| 客户端 | 官方下载链接 |
|:------:|:------------:|
| Karing | [下载](https://github.com/KaringX/karing/releases) |
| FLClash | [下载](https://github.com/chen08209/FlClash/releases) |
| Clash Verge | [下载](https://github.com/clash-verge-rev/clash-verge-rev/releases) |
| Hiddify | [下载](https://github.com/hiddify/hiddify-app/releases) |
| Clash Mi | [下载](https://github.com/KaringX/clashmi/releases) |
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
