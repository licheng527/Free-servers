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
<p style="text-align: center;">吃饭->睡觉->测节点。</p>
</blockquote>

<h4>节点列表：(这里仅展示部分节点)</h4>

```
{chr(10).join(node_links)}
```

<p></p>


<div class="nv-content-wrap entry-content">
<h2>Clash、SS等客户端订阅地址一键转换：</h2>
<p>SS/SSR/V2ray客户端若无法直接使用SSR节点链接，用下面链接的工具转换成订阅地址后，SSR/SSD/Surge/Quantum/Surfboard/Loon等手机、电脑的客户端就可以使用了：</p>
<p><a href="https://acl4ssr-sub.github.io" target="_blank" rel="noreferrer noopener nofollow">https://acl4ssr-sub.github.io</a></p>
<h2>V2ray/SSR安卓苹果手机/电脑客户端下载</h2>
<h3>V2Ray客户端下载</h3>
<p>最新版V2ray Windows客户端、V2ray安卓客户端、苹果电脑V2ray MacOS客户端和苹果手机V2ray iOS客户端以及V2ray Linux客户端下载链接也一并送上。</p>
<h4>Windows7/8/10-<strong>V2ray WinPC电脑客户端</strong>程序下载</h4>
<figure class="wp-block-table alignwide is-style-stripes"><table><tbody><tr><td>V2rayN下载</td><td><a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>V2rayW下载</td><td><a href="https://github.com/Cenmrev/V2RayW/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>Clash下载</td><td><a href="https://github.com/Fndroid/clash_for_windows_pkg/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>V2rayS下载</td><td><a href="https://github.com/Shinlor/V2RayS/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>Mellow下载</td><td><a href="https://github.com/mellow-io/mellow/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>Qv2ray下载</td><td><a href="https://github.com/Qv2ray/Qv2ray" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr></tbody></table></figure>
<h4><strong>Android/小米MIUI/华为EMUI-V2ray安卓手机客户端</strong>Apk程序下载</h4>
<figure class="wp-block-table alignwide is-style-stripes"><table><tbody><tr><td>V2rayNG下载</td><td><a href="https://github.com/2dust/v2rayNG/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>安卓小火箭下载</td><td><a href="https://github.com/Pawdroid/shadowrocket_for_android/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>BifrostV下载</td><td><a rel="noreferrer noopener" href="https://www.appsapk.com/downloading/latest/com.github.dawndiy.bifrostv-0.6.8.apk" target="_blank">市场下载</a></td></tr><tr><td>Clash下载</td><td><a href="https://github.com/Kr328/ClashForAndroid/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>Kitsunebi下载</td><td><a rel="noreferrer noopener" href="https://apkpure.com/kitsunebi/fun.kitsunebi.kitsunebi4android" target="_blank">市场下载</a></td></tr></tbody></table></figure>
<h4><strong>MacOS-V2ray <strong>苹果电脑</strong>客户端</strong>程序下载</h4>
<figure class="wp-block-table alignwide is-style-stripes"><table><tbody><tr><td>V2rayU下载</td><td><a href="https://github.com/yanue/V2rayU/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>V2rayX下载</td><td><a href="https://github.com/Cenmrev/V2RayX/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>ClashX下载</td><td><a href="https://github.com/yichengchen/clashX/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr></tbody></table></figure>
<h4><strong>Linux</strong>–<strong>V2ray Ubuntu/Centos电脑客户端</strong>程序下载</h4>
<figure class="wp-block-table alignwide is-style-stripes"><table><tbody><tr><td>Qv2ray下载</td><td><a href="https://github.com/Qv2ray/Qv2ray" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>Mellow下载</td><td><a href="https://github.com/mellow-io/mellow/releases" target="_blank" rel="noreferrer noopener">官网下载</a></td></tr><tr><td>V2rayL下载</td><td><a rel="noreferrer noopener" href="https://github.com/jiangxufeng/v2rayL" target="_blank">官方安装文档</a></td></tr></tbody></table></figure>
<h4>iOS-<strong>V2ray苹果<strong>手机客户端</strong>App程序</strong>下载</h4>
<p>苹果AppStore市场里还没有免费的V2ray iOS客户端，付费的app目前有小火箭Shadowrocket、pepi、i2Ray、Kitsunebi和Quantumult（圈儿，圈叉）可用。</p>
<h3>ShadowsocksR/SSR客户端下载</h3>
<p>ShadowsocksR简称SSR，还有酸酸乳、粉色小飞机、纸飞机这些可爱的昵称，使用较为广泛。</p>
<p>整理了最新版SSR Windows客户端、SSR安卓客户端、苹果电脑SSR MacOS客户端和苹果手机SSR iOS客户端的下载地址分享给大家。</p>
<h4><strong>Windows7/8/10-<strong>SSR小飞机 WinPC电脑客户端</strong>程序下载</strong></h4>
<p><a rel="noreferrer noopener" href="https://github.com/shadowsocksrr/shadowsocksr-csharp/releases" target="_blank">官网下载</a></p>
<h4><strong><strong>Android/小米MIUI/华为EMUI-SSR小飞机 安卓手机客户端</strong>Apk程序下载</strong></h4>
<p><a rel="noreferrer noopener" href="https://github.com/shadowsocksrr/shadowsocksr-android/releases" target="_blank">官网下载</a></p>
<h4><strong><strong>MacOS-SSR小飞机 苹果电脑客户端</strong>程序下载</strong></h4>
<p><a href="https://github.com/qinyuhang/ShadowsocksX-NG-R/releases" target="_blank" rel="noreferrer noopener">官网下载</a></p>
<h4><strong>iOS-<strong>SSR小飞机 苹果手机客户端App程序</strong></strong>下载</h4>
<p>iPhone或者iPad打开苹果App Store，搜索Mume(暮梅)、Potatso Lite、FastSocks、Shadowrocket（小火箭）。</p></div>
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
