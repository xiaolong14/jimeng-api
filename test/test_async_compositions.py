#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【修改说明 - 2025-12-17】
修改背景: 需要并发验证 /v1/images/compositions 接口，确保多请求稳定返回。
解决问题: 提供异步脚本同时发送 3 个相同请求，并自动落盘响应 JSON。
设计考虑: 使用 aiohttp + asyncio 并发，固定 payload 与 Token 明文写入以便快速测试。
注意事项: 依赖 aiohttp；如需安全请改为从环境变量读取 Token 或调整保存路径。
"""

import asyncio
import json
import random
import time
from pathlib import Path

import aiohttp


API_URL = "http://localhost:5100/v1/images/compositions"
TOKEN = "hk-513aaa456e58cbdede895e1afe22dad9"
OUTPUT_PATH = Path(__file__).parent / "compositions_result.json"

# 固定请求体
PAYLOAD = {
    "model": "jimeng-4.5",
    "prompt": "根据图片，绘制 9个相同画风的分镜。分镜图中绝对不能生出对话框和字幕 ；16：9画幅。每个分镜同等大小，按照9宫格排列，且用白色分割；如果我给你了九宫格分镜图，就强制把九宫格分镜图第九个分镜作为新绘制九宫格的第一个分镜；图一为原图；图二为九宫格分镜图；",
    "images": ["https://gallery-image.spbst.cn/webp/1996842087043039232/6893a162-f8d2-4f45-8c33-ea8e49895dac"],
    "ratio": "16:9",
}

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}


async def call_api(session: aiohttp.ClientSession, index: int) -> dict:
    """
    并发调用 compositions 接口并返回结构化结果。

    【修改说明 - 2025-12-17】
    修改背景: 用户希望在控制台看到每次请求的详细参数与响应内容，便于排查接口异常原因。
    解决问题: 在请求前后打印 URL、Headers(脱敏)、Payload、状态码、耗时和响应文本摘要，并在异常时打印详细异常信息。
    设计考虑: 仅在测试脚本中增加打印，不改变原有 JSON 结果结构；Authorization 头只打印前后若干位以避免完整泄露 Token。
    注意事项: 如在生产环境使用此脚本，建议进一步减少日志内容或移除敏感字段打印。
    【修改说明 - 2025-12-17】
    修改背景: 默认 300 秒超时时间在当前环境下易触发 TimeoutError，影响并发压测结果观察。
    解决问题: 将单次请求的超时时间从 300 秒提升到 600 秒(10 分钟)，给接口更多响应时间。
    设计考虑: 仅放宽客户端超时时间，不改变请求参数与并发数量，方便在本地长耗时场景下验证服务稳定性。
    注意事项: 若接口仍在 600 秒内无响应，依旧会抛出超时异常，请结合服务端日志一并排查。
    【修改说明 - 2025-12-17】
    修改背景: 用户反馈遇到"图片上传网络请求失败"错误时需要自动重试。
    解决问题: 添加特定错误的重试逻辑，使用1-3-5秒指数退避策略重试3次。
    设计考虑: 仅对"fetch failed"类型的网络错误进行重试，其他错误直接返回。
    注意事项: 重试时会重新发送完整请求，确保服务端能够正确处理。
    """
    # 打印请求参数
    masked_headers = dict(HEADERS)
    auth = masked_headers.get("Authorization")
    if isinstance(auth, str) and len(auth) > 16:
        # 仅保留前 10 位和后 6 位，避免完整泄露 Token
        masked_headers["Authorization"] = f"{auth[:10]}...{auth[-6:]}"

    # 定义重试延迟时间（秒）: 1, 3, 5
    retry_delays = [1, 3, 5]

    for attempt in range(4):  # 最多尝试4次（1次初始 + 3次重试）
        start_ts = time.time()

        if attempt > 0:
            delay = retry_delays[attempt - 1]
            print(f"[#{index}] 第 {attempt} 次重试，等待 {delay} 秒...")
            await asyncio.sleep(delay)
            print(f"[#{index}] ===== 重试开始 =====")
        else:
            print(f"[#{index}] ===== 请求开始 =====")

        print(f"[#{index}] URL: {API_URL}")
        print(f"[#{index}] Headers: {json.dumps(masked_headers, ensure_ascii=False)}")
        print(f"[#{index}] Payload: {json.dumps(PAYLOAD, ensure_ascii=False)}")

        try:
            # 【修改说明 - 2025-12-17】
            # 修改背景: 用户反馈 300 秒超时时间不足以等待接口返回结果，经常触发 TimeoutError。
            # 解决问题: 将 timeout 从 300 调整为 600 秒，以支持最长 10 分钟的长耗时请求。
            # 设计考虑: 仅放宽客户端超时阈值，不修改并发数量和业务参数，避免影响其他逻辑。
            async with session.post(API_URL, json=PAYLOAD, headers=HEADERS, timeout=600) as resp:
                raw_text = await resp.text()
                elapsed = time.time() - start_ts
                print(f"[#{index}] 响应状态: {resp.status}, 耗时: {elapsed:.2f}s")
                # 为避免日志过长，仅打印前 500 字符
                preview = raw_text[:500]
                print(f"[#{index}] 响应内容预览(前 500 字符): {preview!r}")

                if resp.status >= 400:
                    print(f"[#{index}] HTTP 错误状态，记录为 error。")
                    return {
                        "index": index,
                        "status": resp.status,
                        "error": raw_text,
                        "retry_count": attempt,
                    }

                try:
                    body = json.loads(raw_text)
                except json.JSONDecodeError:
                    print(f"[#{index}] 响应非 JSON，无法解析为字典。")
                    return {
                        "index": index,
                        "status": resp.status,
                        "error": "响应非JSON",
                        "raw": raw_text,
                        "retry_count": attempt,
                    }

                # 检查是否是需要重试的错误
                if isinstance(body, dict) and body.get("code") == -2007:
                    error_msg = body.get("message", "")
                    if "fetch failed" in error_msg and attempt < 3:
                        print(f"[#{index}] 检测到网络请求失败错误，准备第 {attempt + 1} 次重试...")
                        continue  # 继续下一次重试
                    elif "fetch failed" in error_msg and attempt == 3:
                        print(f"[#{index}] 已重试 3 次仍失败，放弃重试。")
                        return {
                            "index": index,
                            "status": resp.status,
                            "body": body,
                            "retry_count": attempt,
                            "error": "已重试3次仍失败",
                        }

                print(f"[#{index}] 请求成功，已解析为 JSON。")
                return {
                    "index": index,
                    "status": resp.status,
                    "body": body,
                    "retry_count": attempt,
                }

        except asyncio.TimeoutError as exc:
            elapsed = time.time() - start_ts
            print(f"[#{index}] 请求超时({elapsed:.2f}s): {repr(exc)}")
            return {
                "index": index,
                "status": "exception",
                "error": f"请求超时({elapsed:.2f}s): {repr(exc)}",
                "retry_count": attempt,
            }
        except aiohttp.ClientError as exc:
            elapsed = time.time() - start_ts
            print(f"[#{index}] HTTP 客户端异常({elapsed:.2f}s): {repr(exc)}")
            return {
                "index": index,
                "status": "exception",
                "error": f"HTTP 客户端异常: {repr(exc)}",
                "retry_count": attempt,
            }
        except Exception as exc:
            elapsed = time.time() - start_ts
            print(f"[#{index}] 未知异常({elapsed:.2f}s): {repr(exc)}")
            return {
                "index": index,
                "status": "exception",
                "error": f"未知异常: {repr(exc)}",
                "retry_count": attempt,
            }


async def call_api_with_delay(session: aiohttp.ClientSession, index: int, delay: float) -> dict:
    """
    延迟后调用API的包装函数

    【修改说明 - 2025-12-17】
    修改背景: 确保每个请求独立异步执行，避免相互阻塞。
    解决问题: 使用asyncio.sleep()实现延迟启动，然后异步执行请求。
    设计考虑: 每个请求在独立的任务中执行，即使某个请求卡住也不影响其他请求。
    注意事项: 延迟时间只在开始时生效，请求本身仍然是异步并发的。
    """
    if delay > 0:
        print(f"[#{index}] 将在 {delay:.2f} 秒后开始请求...")
        await asyncio.sleep(delay)

    print(f"[#{index}] 开始请求...")
    return await call_api(session, index)


async def main() -> None:
    # 【修改说明 - 2025-12-17】
    # 修改背景: 用户需要每个请求都是独立的异步执行，且每个请求之间间隔2-5秒。
    # 解决问题: 先创建所有异步任务并发执行，然后用asyncio.sleep()在任务之间添加间隔。
    # 设计考虑: 使用异步生成器和asyncio.gather()来实现真正的异步并发和间隔控制。
    # 注意事项: 这种方式确保每个请求都是独立异步的，不会被其他请求阻塞。
    async with aiohttp.ClientSession() as session:
        # 创建异步任务生成器
        async def make_request(index: int):
            return await call_api(session, index)

        print("开始发送异步请求...")

        # 创建3个独立的异步任务
        tasks = []

        # 第一个请求立即发送
        print("发送第 1 个请求...")
        task1 = asyncio.create_task(make_request(1))
        tasks.append(task1)

        # 等待2-5秒后发送第二个请求
        delay1 = random.uniform(2, 5)
        print(f"等待 {delay1:.2f} 秒后发送第 2 个请求...")
        await asyncio.sleep(delay1)
        print("发送第 2 个请求...")
        task2 = asyncio.create_task(make_request(2))
        tasks.append(task2)

        # 再等待2-5秒后发送第三个请求
        delay2 = random.uniform(2, 5)
        print(f"等待 {delay2:.2f} 秒后发送第 3 个请求...")
        await asyncio.sleep(delay2)
        print("发送第 3 个请求...")
        task3 = asyncio.create_task(make_request(3))
        tasks.append(task3)

        print("所有请求已发送，等待响应完成...")

        # 等待所有任务完成（并发执行，不相互阻塞）
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        results = []
        for i, result in enumerate(completed_results):
            if isinstance(result, Exception):
                print(f"请求 #{i+1} 异常: {result}")
                results.append({
                    "index": i + 1,
                    "status": "exception",
                    "error": f"请求异常: {str(result)}",
                })
            else:
                results.append(result)

        print(f"所有请求完成，共处理 {len(results)} 个结果")

    output = {
        "created": int(time.time()),
        "requests": results,
    }

    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 完成，结果已写入: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())

