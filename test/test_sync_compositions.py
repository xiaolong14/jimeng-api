#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【修改说明 - 2025-12-17】
修改背景: 原异步测试脚本所有请求都超时(600秒)，需要同步版本详细捕获响应并分析问题。
解决问题: 创建同步请求脚本，支持更长时间等待，并打印详细的连接、响应信息用于调试。
设计考虑: 使用requests库替代aiohttp，增加更多调试信息，包括连接状态、响应头、响应流等。
注意事项: 此为调试脚本，用于定位超时问题的根本原因。
"""

import json
import time
import socket
from pathlib import Path
from typing import Dict, Any, Optional

import requests


# 配置
API_URL = "http://localhost:5100/v1/images/compositions"
TOKEN = "hk-9cb662e2c1135c389baa78305dcfd729"
OUTPUT_PATH = Path(__file__).parent / "sync_compositions_result.json"

# 固定请求体
PAYLOAD = {
    "model": "jimeng-4.5",
    "prompt": "根据图片，绘制 9个相同画风的分镜。分镜图中绝对不能生出对话框和字幕 ；16：9画幅。每个分镜同等大小，按照9宫格排列，且用白色分割；如果我给你了九宫格分镜图，就强制把九宫格分镜图第九个分镜作为新绘制九宫格的第一个分镜；图一为原图；图二为九宫格分镜图；",
    "images": ["https://gallery-image.spbst.cn/webp/1996842087043039232/6893a162-f8d2-4f45-8c33-ea8e49895dac"],
    "ratio": "16:9",
}

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


def test_connection() -> Dict[str, Any]:
    """测试服务器连接"""
    result = {
        "test_type": "connection_test",
        "success": False,
        "details": {},
        "error": None
    }

    try:
        # 解析URL获取主机和端口
        from urllib.parse import urlparse
        parsed = urlparse(API_URL)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        print(f"=== 连接测试 ===")
        print(f"主机: {host}")
        print(f"端口: {port}")

        # 测试TCP连接
        start_ts = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10秒连接超时

        try:
            sock.connect((host, port))
            conn_time = time.time() - start_ts
            print(f"✅ TCP连接成功，耗时: {conn_time:.2f}s")
            result["success"] = True
            result["details"] = {
                "tcp_connection_time": conn_time,
                "host": host,
                "port": port
            }
        except Exception as e:
            conn_time = time.time() - start_ts
            print(f"❌ TCP连接失败，耗时: {conn_time:.2f}s, 错误: {e}")
            result["error"] = f"TCP连接失败: {e}"
        finally:
            sock.close()

    except Exception as e:
        result["error"] = f"连接测试异常: {e}"
        print(f"❌ 连接测试异常: {e}")

    return result


def call_api_sync(index: int, timeout: int = 1800) -> Dict[str, Any]:
    """
    同步调用 compositions 接口，使用更长的超时时间捕获响应。

    Args:
        index: 请求索引
        timeout: 超时时间（秒），默认30分钟

    Returns:
        请求结果字典
    """
    # 打印请求参数
    masked_headers = dict(HEADERS)
    auth = masked_headers.get("Authorization")
    if isinstance(auth, str) and len(auth) > 16:
        masked_headers["Authorization"] = f"{auth[:10]}...{auth[-6:]}"

    start_ts = time.time()
    print(f"\n[#{index}] ===== 同步请求开始 =====")
    print(f"[#{index}] URL: {API_URL}")
    print(f"[#{index}] 超时设置: {timeout}秒 ({timeout//60}分钟)")
    print(f"[#{index}] Headers: {json.dumps(masked_headers, ensure_ascii=False)}")
    print(f"[#{index}] Payload: {json.dumps(PAYLOAD, ensure_ascii=False)}")

    result = {
        "index": index,
        "start_time": start_ts,
        "status": None,
        "error": None,
        "response_details": {}
    }

    try:
        # 创建session，配置更详细的超时
        with requests.Session() as session:
            # 配置session
            session.headers.update(HEADERS)

            print(f"[#{index}] 开始发送HTTP请求...")
            request_start = time.time()

            # 发送请求，使用非常长的超时时间
            response = session.post(
                API_URL,
                json=PAYLOAD,
                timeout=(
                    30,      # 连接超时：30秒
                    timeout  # 读取超时：30分钟
                ),
                stream=True  # 启用流式响应，便于监控
            )

            request_sent_time = time.time() - request_start
            print(f"[#{index}] 请求发送完成，服务器响应时间: {request_sent_time:.2f}s")
            print(f"[#{index}] HTTP状态码: {response.status_code}")

            # 记录响应头信息
            result["response_details"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "request_sent_time": request_sent_time,
                "encoding": response.encoding
            }

            print(f"[#{index}] 响应头:")
            for key, value in response.headers.items():
                print(f"[#{index}]   {key}: {value}")

            # 检查状态码
            if response.status_code >= 400:
                print(f"[#{index}] HTTP错误状态码: {response.status_code}")
                result["status"] = response.status_code

                # 尝试读取错误响应
                try:
                    error_text = response.text
                    print(f"[#{index}] 错误响应内容: {error_text[:500]!r}")
                    result["error"] = f"HTTP {response.status_code}: {error_text}"
                except Exception as e:
                    print(f"[#{index}] 读取错误响应失败: {e}")
                    result["error"] = f"HTTP {response.status_code}: 无法读取响应"

                return result

            print(f"[#{index}] 开始读取响应内容...")
            read_start = time.time()

            # 尝试逐块读取响应（适用于大响应）
            content_parts = []
            total_read = 0

            try:
                for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                    if chunk:
                        content_parts.append(chunk)
                        total_read += len(chunk)

                        # 每100KB打印一次进度
                        if total_read % (100 * 1024) == 0:
                            elapsed = time.time() - read_start
                            print(f"[#{index}] 已读取: {total_read} 字节, 耗时: {elapsed:.1f}s")

                raw_text = ''.join(content_parts)
                read_time = time.time() - read_start
                print(f"[#{index}] 响应读取完成，总大小: {len(raw_text)} 字节, 耗时: {read_time:.2f}s")

                result["response_details"]["read_time"] = read_time
                result["response_details"]["content_length"] = len(raw_text)

                # 解析JSON
                try:
                    body = json.loads(raw_text)
                    print(f"[#{index}] ✅ JSON解析成功")

                    # 检查响应结构
                    if isinstance(body, dict):
                        keys = list(body.keys())
                        print(f"[#{index}] 响应JSON包含键: {keys}")

                        # 检查是否有异步相关字段
                        if 'task_id' in body:
                            print(f"[#{index}] 检测到task_id: {body['task_id']}")
                        if 'status' in body:
                            print(f"[#{index}] 响应状态: {body['status']}")

                    result["status"] = response.status_code
                    result["body"] = body

                except json.JSONDecodeError as e:
                    print(f"[#{index}] ❌ JSON解析失败: {e}")
                    print(f"[#{index}] 响应内容预览: {raw_text[:1000]!r}")
                    result["status"] = response.status_code
                    result["error"] = f"JSON解析失败: {e}"
                    result["response_details"]["raw_preview"] = raw_text[:1000]

            except Exception as e:
                read_time = time.time() - read_start
                print(f"[#{index}] ❌ 读取响应时异常: {e}, 已尝试读取 {read_time:.2f}s")
                result["error"] = f"读取响应异常: {e}"
                result["response_details"]["read_attempt_time"] = read_time

    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_ts
        print(f"[#{index}] ❌ 请求超时({elapsed:.2f}s): {e}")
        result["error"] = f"请求超时({elapsed:.2f}s): {e}"

    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_ts
        print(f"[#{index}] ❌ 连接错误({elapsed:.2f}s): {e}")
        result["error"] = f"连接错误: {e}"

    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_ts
        print(f"[#{index}] ❌ 请求异常({elapsed:.2f}s): {e}")
        result["error"] = f"请求异常: {e}"

    except Exception as e:
        elapsed = time.time() - start_ts
        print(f"[#{index}] ❌ 未知异常({elapsed:.2f}s): {e}")
        result["error"] = f"未知异常: {e}"

    finally:
        total_elapsed = time.time() - start_ts
        result["total_time"] = total_elapsed
        print(f"[#{index}] 总耗时: {total_elapsed:.2f}s ({total_elapsed/60:.1f}分钟)")

    return result


def main():
    print("🚀 开始同步API测试")
    print(f"API URL: {API_URL}")
    print(f"输出文件: {OUTPUT_PATH}")
    print("=" * 60)

    # 测试连接
    print("\n" + "=" * 60)
    connection_result = test_connection()

    if not connection_result["success"]:
        print(f"\n⚠️  连接测试失败，但继续进行API测试...")
        print(f"   连接错误: {connection_result.get('error', 'Unknown')}")

    print("\n" + "=" * 60)
    print("📡 开始API请求测试")
    print("⏰ 设置超时时间为30分钟，请耐心等待...")

    # 执行单个请求进行详细测试
    result = call_api_sync(1, timeout=1800)  # 30分钟超时

    # 汇总结果
    output = {
        "test_start_time": time.time(),
        "connection_test": connection_result,
        "api_test": result,
        "summary": {
            "total_time": result.get("total_time", 0),
            "success": result.get("error") is None and result.get("status") == 200,
            "error": result.get("error"),
            "status_code": result.get("status"),
        }
    }

    # 保存结果
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("📊 测试总结")
    print(f"✅ 结果已保存到: {OUTPUT_PATH.resolve()}")
    print(f"⏱️  总耗时: {output['summary']['total_time']:.2f}s ({output['summary']['total_time']/60:.1f}分钟)")
    print(f"📝 测试状态: {'成功' if output['summary']['success'] else '失败'}")

    if output['summary']['error']:
        print(f"❌ 错误信息: {output['summary']['error']}")

    if output['summary']['status_code']:
        print(f"🔢 HTTP状态码: {output['summary']['status_code']}")


if __name__ == "__main__":
    main()