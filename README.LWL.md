# 项目介绍文档

项目名称：jimeng-api

> 免费的AI图像和视频生成API服务 - 基于即梦AI的逆向工程实现，提供与OpenAI API兼容的接口格式

---

## 一、项目作用

**核心功能**：提供OpenAI兼容的AI生成API，免费使用即梦AI和Dreamina的图像与视频生成能力

**主要功能模块**：
- **图像生成模块**：支持文本生成图像（文生图）、图像生成图像（图生图）
- **视频生成模块**：支持文本生成视频、图像生成视频、首尾帧视频生成
- **聊天完成模块**：支持对话式交互，可在对话中生成图像内容
- **模型管理模块**：提供支持的AI模型列表和参数信息

---

## 二、快速开始

### 启动项目

```bash
# 方式一：开发环境启动
npm run dev

# 方式二：生产环境启动
npm run build && npm start

# 方式三：Docker启动（推荐）
docker-compose up -d

# 访问地址
http://localhost:5100
```

### 环境要求

- Node.js 18.0+
- TypeScript 5.3.3+
- 8GB+ RAM（推荐）

---

## 三、业务流程

### 主流程

```text
API请求接收
  ↓
参数验证与解析
  ├─→ 验证失败 → 返回错误信息
  └─→ 验证成功 → 调用业务逻辑
  ↓
业务逻辑处理
  ├─→ 调用即梦API → 智能轮询器等待结果
  │   ├─→ 成功 → 格式化响应数据
  │   └─→ 失败 → 重试或返回错误
  └─→ 本地处理（如聊天模型列表）
  ↓
返回OpenAI格式响应
```

### 图像生成流程
用户发起图像生成请求
  ↓
Controller接收请求，验证参数
  ├─→ 参数错误 → 返回400错误
  └─→ 参数正确 → 调用图像生成服务
  ↓
构建即梦API请求
  ├─→ 选择合适的模型（jimeng-4.5等）
  ├─→ 设置分辨率、比例等参数
  └─→ 添加负面提示词（可选）
  ↓
提交到即梦AI服务
  ├─→ 智能轮询器监控任务状态
  ├─→ 自动调整轮询间隔
  └─→ 任务完成或失败后返回
  ↓
转换为OpenAI格式返回

### 关键说明

- **智能轮询器**：自适应调整轮询频率，避免频繁请求
- **错误处理**：统一异常处理机制，自动重试失败的请求
- **响应格式**：完全兼容OpenAI API格式，可直接替换使用
- **多站点支持**：自动选择最优的服务站点（国内/国外）

---

## 四、常用操作

| 操作 | 接口 | 说明 |
|------|------|------|
| 文生图 | `POST /v1/images/generations` | 根据文本描述生成图像 |
| 图生图 | `POST /v1/images/compositions` | 基于输入图像生成新图像 |
| 文生视频 | `POST /v1/videos/generations` | 根据文本生成视频 |
| 图生视频 | `POST /v1/videos/generations` | 根据图像生成视频 |
| 聊天对话 | `POST /v1/chat/completions` | 对话式交互，支持生成图像 |
| 获取模型 | `GET /v1/models` | 查看所有可用的AI模型 |
| 健康检查 | `GET /ping` | 检查服务运行状态 |
| 获取Token | `POST /token` | 获取访问令牌 |

### 请求示例

```bash
# 文生图请求
curl -X POST http://localhost:5100/v1/images/generations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "jimeng-4.5",
    "prompt": "一只可爱的猫",
    "size": "1024x1024"
  }'

# 获取模型列表
curl http://localhost:5100/v1/models
```

---

## 五、注意事项

- ⚠️ **Token配置**：使用前需要配置有效的sessionid作为Bearer Token
- ⚠️ **请求限制**：为避免对官方服务器造成压力，请合理控制请求频率
- ⚠️ **合规使用**：仅用于学习和研究目的，不得用于商业用途
- ⚠️ **版本兼容**：API接口与OpenAI格式完全兼容，可直接替换使用
- ⚠️ **资源占用**：视频生成需要较长时间，请耐心等待
- ⚠️ **模型选择**：不同模型支持的功能和参数可能不同，请查看模型列表

### 支持的模型

- **图像模型**：jimeng-2.0, jimeng-3.0, jimeng-3.1, jimeng-4.0, jimeng-4.1, jimeng-4.5
- **视频模型**：jimeng-video-2.0, jimeng-video-3.0, jimeng-video-3.0-pro, jimeng-video-3.0-fast
- **聊天模型**：jimeng-chat等

### 支持的服务站点

- 即梦AI国内站：https://jimeng.jianying.com
- Dreamina美国站：https://commerce.us.capcut.com
- Dreamina香港站：https://commerce-api-sg.capcut.com
- Dreamina日本站：https://mweb-api-sg.capcut.com

---

**最后更新**：2025-12-16
