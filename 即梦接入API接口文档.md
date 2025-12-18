# 即梦接入API接口文档

## 一、接口说明

### 1.1 基础信息
- **基础路径**：`/api/jimeng`
- **协议**：HTTP/HTTPS
- **数据格式**：JSON
- **字符编码**：UTF-8

### 1.2 统一响应格式

#### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": 1705123456789
}
```

#### 失败响应
```json
{
  "code": 400,
  "message": "错误描述",
  "data": null,
  "timestamp": 1705123456789
}
```

#### 分页响应
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [],
    "total": 100,
    "page": 1,
    "pageSize": 10,
    "totalPages": 10
  },
  "timestamp": 1705123456789
}
```

### 1.3 状态码说明
- `200`：成功
- `400`：请求参数错误
- `401`：未授权
- `403`：禁止访问
- `404`：资源不存在
- `500`：服务器内部错误

### 1.4 通用参数说明
- `create_by`：创建人，系统自动从当前登录用户获取
- `update_by`：修改人，系统自动从当前登录用户获取
- `is_deleted`：逻辑删除标记，0-未删除，1-已删除

---

## 二、账号管理接口

### 2.1 创建账号接口

**接口地址**：`POST /api/jimeng/accounts/create`

**功能说明**：批量创建即梦账号，支持一次创建多个账号

**请求参数**：
```json
[
  {
    "jimeng_account": "账号1@example.com",
    "jimeng_account_type": 0,
    "session_id": "session_id_1"
  },
  {
    "jimeng_account": "账号2@example.com",
    "jimeng_account_type": 1,
    "session_id": "session_id_2"
  }
]
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| jimeng_account | String | 否 | 即梦账号，如邮箱 |
| jimeng_account_type | Integer | 否 | 账号类型：0-国内账号，1-国外账号，默认0 |
| session_id | String | 否 | 登录状态ID |

**业务规则**：
1. 数组不允许为空，至少包含一个账号对象
2. `site_type`：根据`jimeng_account_type`决定
   - 如果`jimeng_account_type`为0（国内账号），`site_type`默认为0（cn）
   - 如果`jimeng_account_type`为1（国外账号），`site_type`默认为2（hk）
3. `quota_reset_time`：额度重置时间，由应用在账号创建时写入为"创建日期+1天的0:30"
   - 例如：创建时间为2025-01-16 10:00:00，则`quota_reset_time`为2025-01-17 00:30:00
4. `create_by`：自动从当前登录用户获取
5. `account_status`：默认为0（active）
6. `image_generation_status`：默认为1（可用）
7. `video_generation_status`：默认为1（可用）
8. `priority`：默认为0
9. `max_retry_count`：默认为4
10. 如果`session_id`和`site_type`的组合已存在，则返回错误

**处理流程**：
1. 验证请求参数（数组不为空，参数格式正确）
2. 遍历账号数组，对每个账号：
   - 生成UUID作为`id`
   - 根据`jimeng_account_type`设置`site_type`
   - 计算`quota_reset_time`（创建时间+1天+0:30）
   - 设置默认值（状态、优先级等）
   - 获取当前登录用户作为`create_by`
   - 检查`(session_id, site_type)`唯一性
   - 插入数据库
3. 返回创建结果

**响应示例**：
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "successCount": 2,
    "failedCount": 0,
    "results": [
      {
        "id": "uuid-1",
        "jimeng_account": "账号1@example.com",
        "status": "success"
      },
      {
        "id": "uuid-2",
        "jimeng_account": "账号2@example.com",
        "status": "success"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**错误响应**：
```json
{
  "code": 400,
  "message": "账号数组不能为空",
  "data": null,
  "timestamp": 1705123456789
}
```

**备注**：
- 支持批量创建，建议单次不超过100个账号
- 如果部分账号创建失败，会返回成功和失败的详细信息
- `session_id`和`site_type`的组合必须唯一

---

### 2.2 修改账号接口

**接口地址**：`POST /api/jimeng/accounts/update`

**功能说明**：批量修改即梦账号信息

**请求参数**：
```json
[
  {
    "id": "uuid-1",
    "jimeng_account": "新账号1@example.com",
    "jimeng_account_type": 0,
    "session_id": "new_session_id_1"
  },
  {
    "id": "uuid-2",
    "jimeng_account": "新账号2@example.com",
    "jimeng_account_type": 1,
    "session_id": "new_session_id_2"
  }
]
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | 账号ID（UUID） |
| jimeng_account | String | 否 | 即梦账号 |
| jimeng_account_type | Integer | 否 | 账号类型：0-国内账号，1-国外账号 |
| session_id | String | 否 | 登录状态ID |

**业务规则**：
1. 数组不允许为空，至少包含一个账号对象
2. `id`为必填项，用于定位要修改的账号
3. `site_type`：如果提供了`jimeng_account_type`，根据其值更新`site_type`
   - 如果`jimeng_account_type`为0（国内账号），`site_type`更新为0（cn）
   - 如果`jimeng_account_type`为1（国外账号），`site_type`更新为2（hk）
4. `update_by`：自动从当前登录用户获取
5. `update_time`：自动更新为当前时间
6. 只更新提供的字段，未提供的字段保持不变
7. 如果账号不存在或已删除，返回错误

**处理流程**：
1. 验证请求参数（数组不为空，id必填）
2. 遍历账号数组，对每个账号：
   - 根据`id`查询账号是否存在且未删除
   - 如果不存在，记录错误并跳过
   - 如果提供了`jimeng_account_type`，更新`site_type`
   - 更新提供的字段
   - 获取当前登录用户作为`update_by`
   - 更新数据库
3. 返回修改结果

**响应示例**：
```json
{
  "code": 200,
  "message": "修改成功",
  "data": {
    "successCount": 2,
    "failedCount": 0,
    "results": [
      {
        "id": "uuid-1",
        "status": "success"
      },
      {
        "id": "uuid-2",
        "status": "success"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**错误响应**：
```json
{
  "code": 404,
  "message": "账号不存在：uuid-1",
  "data": null,
  "timestamp": 1705123456789
}
```

**备注**：
- 支持批量修改，建议单次不超过100个账号
- 如果部分账号修改失败，会返回成功和失败的详细信息
- 修改`session_id`时，需要检查新的`(session_id, site_type)`组合是否已存在

---

### 2.3 查询账号接口（分页）

**接口地址**：`GET /api/jimeng/accounts/list`

**功能说明**：根据创建人分页查询账号列表

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| create_by | String | 是 | 创建人 |
| page | Integer | 否 | 页码，默认1 |
| pageSize | Integer | 否 | 每页数量，默认10，最大100 |
| account_status | Integer | 否 | 账号状态筛选：0-active，1-inactive，2-banned |
| image_generation_status | Integer | 否 | 生图状态筛选：0-不可用，1-可用，2-速率限制 |
| video_generation_status | Integer | 否 | 生视频状态筛选：0-不可用，1-可用，2-速率限制 |
| site_type | Integer | 否 | 站点类型筛选：0-cn，1-us，2-hk，3-jp，4-sg |
| orderBy | String | 否 | 排序字段，默认create_time |
| order | String | 否 | 排序方式，asc/desc，默认desc |

**请求示例**：
```
GET /api/jimeng/accounts/list?create_by=user123&page=1&pageSize=20&account_status=0
```

**业务规则**：
1. `create_by`为必填项，用于筛选账号
2. 只查询未删除的账号（`is_deleted=0`）
3. 支持多条件组合筛选
4. 默认按创建时间倒序排列

**处理流程**：
1. 验证请求参数（`create_by`必填，`page`和`pageSize`范围校验）
2. 构建查询条件：
   - `create_by` = 请求参数
   - `is_deleted` = 0
   - 根据可选参数添加筛选条件
3. 执行分页查询
4. 返回分页结果

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "uuid-1",
        "jimeng_account": "账号1@example.com",
        "jimeng_account_type": 0,
        "session_id": "session_id_1",
        "site_type": 0,
        "account_status": 0,
        "image_generation_status": 1,
        "video_generation_status": 1,
        "image_count": 5,
        "video_count": 2,
        "quota_reset_time": "2025-01-17 00:30:00",
        "priority": 0,
        "create_time": "2025-01-16 10:00:00",
        "update_time": "2025-01-16 10:00:00",
        "create_by": "user123"
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20,
    "totalPages": 3
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 支持多条件组合筛选，提高查询灵活性
- 返回完整的账号信息，便于前端展示和管理

---

### 2.4 删除账号接口

**接口地址**：`DELETE /api/jimeng/accounts/delete`

**功能说明**：逻辑删除账号（软删除）

**请求参数**：
```json
{
  "ids": ["uuid-1", "uuid-2"]
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ids | Array<String> | 是 | 账号ID数组 |

**业务规则**：
1. `ids`数组不能为空
2. 执行逻辑删除，设置`is_deleted=1`
3. `update_by`：自动从当前登录用户获取
4. `update_time`：自动更新为当前时间
5. 如果账号不存在或已删除，跳过该账号

**处理流程**：
1. 验证请求参数（`ids`数组不为空）
2. 遍历`ids`数组，对每个账号：
   - 根据`id`查询账号是否存在且未删除
   - 如果不存在或已删除，记录并跳过
   - 设置`is_deleted=1`
   - 获取当前登录用户作为`update_by`
   - 更新数据库
3. 返回删除结果

**响应示例**：
```json
{
  "code": 200,
  "message": "删除成功",
  "data": {
    "successCount": 2,
    "failedCount": 0,
    "results": [
      {
        "id": "uuid-1",
        "status": "success"
      },
      {
        "id": "uuid-2",
        "status": "success"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 逻辑删除，数据不会真正删除，可以恢复
- 支持批量删除

---

## 三、图片生成接口

### 3.1 分镜文生图接口

**接口地址**：`POST /api/jimeng/images/generate-from-text`

**功能说明**：基于分镜描述词批量生成图片，支持批量分镜同时生成

**请求参数**：
```json
{
  "project_id": "project-123",
  "project_name": "测试项目",
  "work_id": "work-456",
  "tasks": [
    {
      "storyboard_id": "storyboard-1",
      "prompt": "一只可爱的小猫咪，动漫风格",
      "model": "jimeng-4.5",
      "ratio": "16:9",
      "resolution": "2k",
      "negative_prompt": "模糊，低质量",
      "intelligent_ratio": false,
      "priority": 0
    },
    {
      "storyboard_id": "storyboard-2",
      "prompt": "壮丽的山水风景，超高分辨率",
      "model": "jimeng-4.5",
      "ratio": "4:3",
      "resolution": "4k",
      "negative_prompt": "模糊，低质量",
      "intelligent_ratio": false,
      "priority": 0
    }
  ],
  "callback_url": "https://example.com/callback"
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 推理项目ID |
| project_name | String | 是 | 推理项目名称 |
| work_id | String | 是 | 作品ID |
| tasks | Array | 是 | 生成任务数组，至少包含一个任务 |
| tasks[].storyboard_id | String | 是 | 分镜ID |
| tasks[].prompt | String | 是 | 生成提示词 |
| tasks[].model | String | 否 | 使用的模型，默认jimeng-4.5 |
| tasks[].ratio | String | 否 | 宽高比，默认1:1 |
| tasks[].resolution | String | 否 | 分辨率，默认2k |
| tasks[].negative_prompt | String | 否 | 负面提示词 |
| tasks[].intelligent_ratio | Boolean | 否 | 是否启用智能比例，默认false |
| tasks[].priority | Integer | 否 | 任务优先级，默认0 |
| callback_url | String | 否 | 回调地址 |

**业务规则**：
1. `tasks`数组不能为空，至少包含一个任务
2. 每个任务的`storyboard_id`在同一`project_id`下必须唯一
3. 如果该分镜已存在未删除的记录，则返回错误（需要先删除或使用重新生成接口）
4. 账号分配：从账号池中随机分配可用账号（`image_generation_status=1`）
5. 账号切换：如果账号出现问题，自动切换到其他可用账号重试
6. `create_by`：自动从当前登录用户获取

**处理流程**：
1. 验证请求参数（必填项校验，`tasks`数组不为空）
2. 检查分镜唯一性：遍历`tasks`，检查`(project_id, storyboard_id, is_deleted=0)`是否已存在
3. 为每个任务创建生成记录：
   - 生成UUID作为`id`
   - 从账号池随机分配可用账号（`image_generation_status=1`）
   - 设置状态为`pending`
   - 保存生成参数
   - 获取当前登录用户作为`create_by`
4. 异步执行生成任务：
   - 更新状态为`processing`
   - 调用即梦API生成图片
   - 如果账号错误，自动切换账号重试
   - 生成完成后更新状态为`completed`或`failed`
   - 记录生成结果、错误信息、切换次数等
5. 如果提供了`callback_url`，生成完成后进行回调
6. 返回任务创建结果

**响应示例**：
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "taskCount": 2,
    "tasks": [
      {
        "id": "record-uuid-1",
        "storyboard_id": "storyboard-1",
        "status": "pending",
        "message": "任务已创建，正在处理中"
      },
      {
        "id": "record-uuid-2",
        "storyboard_id": "storyboard-2",
        "status": "pending",
        "message": "任务已创建，正在处理中"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 支持批量生成，建议单次不超过50个任务
- 生成过程是异步的，接口立即返回，实际生成结果通过回调或查询接口获取
- 账号自动切换机制对用户透明，记录切换次数和原因

---

### 3.2 分镜图生图接口

**接口地址**：`POST /api/jimeng/images/generate-from-image`

**功能说明**：基于图片和描述词批量生成图片，支持批量分镜同时生成

**请求参数**：
```json
{
  "project_id": "project-123",
  "project_name": "测试项目",
  "work_id": "work-456",
  "tasks": [
    {
      "storyboard_id": "storyboard-1",
      "prompt": "将这张照片转换为油画风格，色彩鲜艳",
      "input_images": [
        "https://example.com/image1.jpg"
      ],
      "model": "jimeng-4.5",
      "ratio": "1:1",
      "resolution": "2k",
      "negative_prompt": "模糊，低质量",
      "sample_strength": 0.7,
      "intelligent_ratio": false,
      "priority": 0
    }
  ],
  "callback_url": "https://example.com/callback"
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 推理项目ID |
| project_name | String | 是 | 推理项目名称 |
| work_id | String | 是 | 作品ID |
| tasks | Array | 是 | 生成任务数组 |
| tasks[].storyboard_id | String | 是 | 分镜ID |
| tasks[].prompt | String | 是 | 生成提示词 |
| tasks[].input_images | Array<String> | 是 | 输入图片URL数组，1-10张 |
| tasks[].model | String | 否 | 使用的模型，默认jimeng-4.5 |
| tasks[].ratio | String | 否 | 宽高比，默认1:1 |
| tasks[].resolution | String | 否 | 分辨率，默认2k |
| tasks[].negative_prompt | String | 否 | 负面提示词 |
| tasks[].sample_strength | Number | 否 | 采样强度，0.0-1.0 |
| tasks[].intelligent_ratio | Boolean | 否 | 是否启用智能比例，默认false |
| tasks[].priority | Integer | 否 | 任务优先级，默认0 |
| callback_url | String | 否 | 回调地址 |

**业务规则**：
1. `input_images`数组不能为空，支持1-10张图片
2. 其他规则与分镜文生图接口相同

**处理流程**：
1. 验证请求参数（包括`input_images`数组校验）
2. 其他流程与分镜文生图接口相同

**响应示例**：
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "taskCount": 1,
    "tasks": [
      {
        "id": "record-uuid-1",
        "storyboard_id": "storyboard-1",
        "status": "pending",
        "message": "任务已创建，正在处理中"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 支持本地文件上传和网络图片URL两种方式
- 如果同时提供本地文件和URL，优先使用本地文件

---

### 3.3 重新生成图片接口

**接口地址**：`POST /api/jimeng/images/regenerate`

**功能说明**：基于分镜ID重新生成图片，覆盖原本的相应记录

**请求参数**：
```json
{
  "project_id": "project-123",
  "storyboard_id": "storyboard-1",
  "prompt": "新的提示词",
  "model": "jimeng-4.5",
  "ratio": "16:9",
  "resolution": "2k",
  "negative_prompt": "新的负面提示词",
  "intelligent_ratio": false,
  "input_images": ["https://example.com/image1.jpg"],
  "priority": 0,
  "callback_url": "https://example.com/callback"
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 推理项目ID |
| storyboard_id | String | 是 | 分镜ID |
| prompt | String | 否 | 新的生成提示词，不提供则使用原提示词 |
| model | String | 否 | 新的模型，不提供则使用原模型 |
| ratio | String | 否 | 新的宽高比，不提供则使用原宽高比 |
| resolution | String | 否 | 新的分辨率，不提供则使用原分辨率 |
| negative_prompt | String | 否 | 新的负面提示词 |
| intelligent_ratio | Boolean | 否 | 是否启用智能比例 |
| input_images | Array<String> | 否 | 输入图片URL数组（图生图时使用） |
| priority | Integer | 否 | 任务优先级 |
| callback_url | String | 否 | 回调地址 |

**业务规则**：
1. `project_id`和`storyboard_id`为必填项，用于定位原记录
2. 根据`(project_id, storyboard_id, is_deleted=0)`查询原记录
3. 如果原记录不存在，返回错误
4. 覆盖机制：
   - 更新原记录的状态为`pending`
   - 清空原结果（`image_urls`、`image_local_paths`）
   - 清空错误信息（`error_code`、`error_message`）
   - 重置`site_switch_count`为0
   - 如果提供了新参数，更新生成参数
   - 保留`jimeng_accounts_id`，但生成时会重新分配账号
5. 重新生成流程与分镜文生图/图生图接口相同

**处理流程**：
1. 验证请求参数（`project_id`和`storyboard_id`必填）
2. 查询原记录：
   - 根据`(project_id, storyboard_id, is_deleted=0)`查询
   - 如果不存在，返回错误
3. 更新原记录：
   - 设置状态为`pending`
   - 清空原结果和错误信息
   - 重置`site_switch_count`为0
   - 如果提供了新参数，更新生成参数
   - 获取当前登录用户作为`update_by`
4. 重新分配账号：从账号池随机分配可用账号
5. 异步执行生成任务（流程与分镜文生图接口相同）
6. 返回重新生成结果

**响应示例**：
```json
{
  "code": 200,
  "message": "重新生成任务已创建",
  "data": {
    "id": "record-uuid-1",
    "storyboard_id": "storyboard-1",
    "status": "pending",
    "message": "任务已创建，正在处理中"
  },
  "timestamp": 1705123456789
}
```

**错误响应**：
```json
{
  "code": 404,
  "message": "原记录不存在",
  "data": null,
  "timestamp": 1705123456789
}
```

**备注**：
- 重新生成会覆盖原记录，原结果会被清空
- 支持更新生成参数，不提供的参数保持原值
- 重新生成时会重新分配账号

---

### 3.4 查询图片生成记录接口（分页）

**接口地址**：`GET /api/jimeng/images/records`

**功能说明**：根据创建人、作品ID分页查询图片生成记录

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| create_by | String | 是 | 创建人 |
| work_id | String | 是 | 作品ID |
| page | Integer | 否 | 页码，默认1 |
| pageSize | Integer | 否 | 每页数量，默认10，最大100 |
| project_id | String | 否 | 推理项目ID筛选 |
| storyboard_id | String | 否 | 分镜ID筛选 |
| generation_status | Integer | 否 | 生成状态筛选：0-pending，1-processing，2-completed，3-failed，4-retrying |
| model | String | 否 | 模型筛选 |
| orderBy | String | 否 | 排序字段，默认create_time |
| order | String | 否 | 排序方式，asc/desc，默认desc |

**请求示例**：
```
GET /api/jimeng/images/records?create_by=user123&work_id=work-456&page=1&pageSize=20&generation_status=2
```

**业务规则**：
1. `create_by`和`work_id`为必填项
2. 只查询未删除的记录（`is_deleted=0`）
3. 支持多条件组合筛选
4. 默认按创建时间倒序排列

**处理流程**：
1. 验证请求参数（`create_by`和`work_id`必填，`page`和`pageSize`范围校验）
2. 构建查询条件：
   - `create_by` = 请求参数
   - `work_id` = 请求参数
   - `is_deleted` = 0
   - 根据可选参数添加筛选条件
3. 执行分页查询
4. 返回分页结果

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "record-uuid-1",
        "jimeng_accounts_id": "account-uuid-1",
        "project_id": "project-123",
        "project_name": "测试项目",
        "storyboard_id": "storyboard-1",
        "work_id": "work-456",
        "model": "jimeng-4.5",
        "prompt": "一只可爱的小猫咪",
        "ratio": "16:9",
        "resolution": "2k",
        "generation_status": 2,
        "image_urls": [
          "https://example.com/image1.jpg"
        ],
        "generation_time": 30,
        "site_switch_count": 0,
        "create_time": "2025-01-16 10:00:00",
        "update_time": "2025-01-16 10:05:00",
        "create_by": "user123"
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20,
    "totalPages": 3
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 支持多条件组合筛选，便于查找特定记录
- 返回完整的生成记录信息，包括生成结果、错误信息等

---

### 3.5 删除图片生成记录接口

**接口地址**：`DELETE /api/jimeng/images/records/delete`

**功能说明**：逻辑删除图片生成记录（软删除）

**请求参数**：
```json
{
  "ids": ["record-uuid-1", "record-uuid-2"]
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ids | Array<String> | 是 | 记录ID数组 |

**业务规则**：
1. `ids`数组不能为空
2. 执行逻辑删除，设置`is_deleted=1`
3. `update_by`：自动从当前登录用户获取
4. `update_time`：自动更新为当前时间

**处理流程**：
1. 验证请求参数（`ids`数组不为空）
2. 遍历`ids`数组，对每个记录：
   - 根据`id`查询记录是否存在且未删除
   - 如果不存在或已删除，记录并跳过
   - 设置`is_deleted=1`
   - 获取当前登录用户作为`update_by`
   - 更新数据库
3. 返回删除结果

**响应示例**：
```json
{
  "code": 200,
  "message": "删除成功",
  "data": {
    "successCount": 2,
    "failedCount": 0,
    "results": [
      {
        "id": "record-uuid-1",
        "status": "success"
      },
      {
        "id": "record-uuid-2",
        "status": "success"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 逻辑删除，数据不会真正删除
- 支持批量删除

---

## 四、视频生成接口

### 4.1 分镜生视频接口

**接口地址**：`POST /api/jimeng/videos/generate`

**功能说明**：基于分镜描述词批量生成视频，支持文生视频、图生视频、首尾帧视频，支持批量分镜同时生成

**请求参数**：
```json
{
  "project_id": "project-123",
  "project_name": "测试项目",
  "work_id": "work-456",
  "tasks": [
    {
      "storyboard_id": "storyboard-1",
      "prompt": "一只奔跑在草原上的狮子",
      "model": "jimeng-video-3.0",
      "ratio": "16:9",
      "resolution": "1080p",
      "duration": 10,
      "negative_prompt": "模糊，低质量",
      "priority": 0
    },
    {
      "storyboard_id": "storyboard-2",
      "prompt": "一个女人在花园里跳舞",
      "model": "jimeng-video-3.0",
      "ratio": "9:16",
      "resolution": "720p",
      "duration": 5,
      "input_images": [
        "https://example.com/first-frame.jpg"
      ],
      "negative_prompt": "模糊，低质量",
      "priority": 0
    },
    {
      "storyboard_id": "storyboard-3",
      "prompt": "场景之间的平滑过渡",
      "model": "jimeng-video-3.0",
      "ratio": "16:9",
      "resolution": "1080p",
      "duration": 10,
      "input_images": [
        "https://example.com/first-frame.jpg",
        "https://example.com/last-frame.jpg"
      ],
      "negative_prompt": "模糊，低质量",
      "priority": 0
    }
  ],
  "callback_url": "https://example.com/callback"
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 推理项目ID |
| project_name | String | 是 | 推理项目名称 |
| work_id | String | 是 | 作品ID |
| tasks | Array | 是 | 生成任务数组 |
| tasks[].storyboard_id | String | 是 | 分镜ID |
| tasks[].prompt | String | 是 | 生成提示词 |
| tasks[].model | String | 否 | 使用的模型，默认jimeng-video-3.0 |
| tasks[].ratio | String | 否 | 宽高比，默认16:9（图生视频时会被忽略） |
| tasks[].resolution | String | 否 | 视频分辨率，默认720p |
| tasks[].duration | Integer | 否 | 视频时长(秒)，默认5，支持5或10 |
| tasks[].input_images | Array<String> | 否 | 输入图片URL数组，0-2张 |
| tasks[].negative_prompt | String | 否 | 负面提示词 |
| tasks[].priority | Integer | 否 | 任务优先级，默认0 |
| callback_url | String | 否 | 回调地址 |

**业务规则**：
1. `tasks`数组不能为空，至少包含一个任务
2. 生成模式自动判断：
   - 无图片 → 文生视频模式
   - 1张图片 → 图生视频模式（作为首帧）
   - 2张图片 → 首尾帧视频模式（第1张为首帧，第2张为尾帧）
3. 如果提供了图片，`ratio`参数会被忽略，视频比例由输入图片决定
4. 其他规则与分镜文生图接口相同

**处理流程**：
1. 验证请求参数（必填项校验，`tasks`数组不为空）
2. 检查分镜唯一性：遍历`tasks`，检查`(project_id, storyboard_id, is_deleted=0)`是否已存在
3. 为每个任务创建生成记录：
   - 生成UUID作为`id`
   - 从账号池随机分配可用账号（`video_generation_status=1`）
   - 设置状态为`pending`
   - 保存生成参数
   - 获取当前登录用户作为`create_by`
4. 异步执行生成任务：
   - 更新状态为`processing`
   - 调用即梦API生成视频
   - 如果账号错误，自动切换账号重试
   - 生成完成后更新状态为`completed`或`failed`
   - 记录生成结果、错误信息、切换次数等
5. 如果提供了`callback_url`，生成完成后进行回调
6. 返回任务创建结果

**响应示例**：
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "taskCount": 3,
    "tasks": [
      {
        "id": "record-uuid-1",
        "storyboard_id": "storyboard-1",
        "status": "pending",
        "message": "任务已创建，正在处理中"
      },
      {
        "id": "record-uuid-2",
        "storyboard_id": "storyboard-2",
        "status": "pending",
        "message": "任务已创建，正在处理中"
      },
      {
        "id": "record-uuid-3",
        "storyboard_id": "storyboard-3",
        "status": "pending",
        "message": "任务已创建，正在处理中"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 支持三种生成模式，系统自动判断
- 文生视频、图生视频、首尾帧视频返回格式一致，不做区分
- 生成过程是异步的，接口立即返回

---

### 4.2 重新生成视频接口

**接口地址**：`POST /api/jimeng/videos/regenerate`

**功能说明**：基于分镜ID重新生成视频，覆盖原本的相应记录

**请求参数**：
```json
{
  "project_id": "project-123",
  "storyboard_id": "storyboard-1",
  "prompt": "新的提示词",
  "model": "jimeng-video-3.0",
  "ratio": "16:9",
  "resolution": "1080p",
  "duration": 10,
  "negative_prompt": "新的负面提示词",
  "input_images": [
    "https://example.com/first-frame.jpg"
  ],
  "priority": 0,
  "callback_url": "https://example.com/callback"
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | String | 是 | 推理项目ID |
| storyboard_id | String | 是 | 分镜ID |
| prompt | String | 否 | 新的生成提示词，不提供则使用原提示词 |
| model | String | 否 | 新的模型，不提供则使用原模型 |
| ratio | String | 否 | 新的宽高比，不提供则使用原宽高比 |
| resolution | String | 否 | 新的分辨率，不提供则使用原分辨率 |
| duration | Integer | 否 | 新的视频时长，不提供则使用原时长 |
| negative_prompt | String | 否 | 新的负面提示词 |
| input_images | Array<String> | 否 | 输入图片URL数组 |
| priority | Integer | 否 | 任务优先级 |
| callback_url | String | 否 | 回调地址 |

**业务规则**：
1. 与重新生成图片接口规则相同
2. 覆盖机制相同

**处理流程**：
1. 与重新生成图片接口流程相同
2. 调用视频生成API

**响应示例**：
```json
{
  "code": 200,
  "message": "重新生成任务已创建",
  "data": {
    "id": "record-uuid-1",
    "storyboard_id": "storyboard-1",
    "status": "pending",
    "message": "任务已创建，正在处理中"
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 重新生成会覆盖原记录，原结果会被清空
- 支持更新生成参数

---

### 4.3 查询视频生成记录接口（分页）

**接口地址**：`GET /api/jimeng/videos/records`

**功能说明**：根据创建人、作品ID分页查询视频生成记录

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| create_by | String | 是 | 创建人 |
| work_id | String | 是 | 作品ID |
| page | Integer | 否 | 页码，默认1 |
| pageSize | Integer | 否 | 每页数量，默认10，最大100 |
| project_id | String | 否 | 推理项目ID筛选 |
| storyboard_id | String | 否 | 分镜ID筛选 |
| generation_status | Integer | 否 | 生成状态筛选：0-pending，1-processing，2-completed，3-failed，4-retrying |
| model | String | 否 | 模型筛选 |
| orderBy | String | 否 | 排序字段，默认create_time |
| order | String | 否 | 排序方式，asc/desc，默认desc |

**请求示例**：
```
GET /api/jimeng/videos/records?create_by=user123&work_id=work-456&page=1&pageSize=20&generation_status=2
```

**业务规则**：
1. 与查询图片生成记录接口规则相同

**处理流程**：
1. 与查询图片生成记录接口流程相同

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "record-uuid-1",
        "jimeng_accounts_id": "account-uuid-1",
        "project_id": "project-123",
        "project_name": "测试项目",
        "storyboard_id": "storyboard-1",
        "work_id": "work-456",
        "model": "jimeng-video-3.0",
        "prompt": "一只奔跑在草原上的狮子",
        "ratio": "16:9",
        "resolution": "1080p",
        "duration": 10,
        "generation_status": 2,
        "video_urls": [
          "https://example.com/video1.mp4"
        ],
        "generation_time": 120,
        "site_switch_count": 1,
        "create_time": "2025-01-16 10:00:00",
        "update_time": "2025-01-16 10:10:00",
        "create_by": "user123"
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20,
    "totalPages": 3
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 支持多条件组合筛选
- 返回完整的生成记录信息

---

### 4.4 删除视频生成记录接口

**接口地址**：`DELETE /api/jimeng/videos/records/delete`

**功能说明**：逻辑删除视频生成记录（软删除）

**请求参数**：
```json
{
  "ids": ["record-uuid-1", "record-uuid-2"]
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ids | Array<String> | 是 | 记录ID数组 |

**业务规则**：
1. 与删除图片生成记录接口规则相同

**处理流程**：
1. 与删除图片生成记录接口流程相同

**响应示例**：
```json
{
  "code": 200,
  "message": "删除成功",
  "data": {
    "successCount": 2,
    "failedCount": 0,
    "results": [
      {
        "id": "record-uuid-1",
        "status": "success"
      },
      {
        "id": "record-uuid-2",
        "status": "success"
      }
    ]
  },
  "timestamp": 1705123456789
}
```

**备注**：
- 逻辑删除，数据不会真正删除
- 支持批量删除

---

## 五、错误码说明

### 5.1 通用错误码
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 5.2 业务错误码
| 错误码 | 说明 |
|--------|------|
| 40001 | 账号数组不能为空 |
| 40002 | 账号ID不能为空 |
| 40003 | 账号不存在 |
| 40004 | 账号已删除 |
| 40005 | session_id和site_type组合已存在 |
| 40006 | 任务数组不能为空 |
| 40007 | 分镜ID不能为空 |
| 40008 | 分镜记录已存在，请使用重新生成接口 |
| 40009 | 原记录不存在 |
| 40010 | 创建人不能为空 |
| 40011 | 作品ID不能为空 |
| 40012 | 输入图片数组不能为空（图生图/图生视频） |
| 40013 | 输入图片数量超出限制（最多10张） |

---

## 六、附录

### 6.1 账号状态说明
- `account_status`：0-active（正常），1-inactive（停用），2-banned（封禁）
- `image_generation_status`：0-不可用，1-可用，2-速率限制
- `video_generation_status`：0-不可用，1-可用，2-速率限制

### 6.2 生成状态说明
- `generation_status`：0-pending（待处理），1-processing（处理中），2-completed（已完成），3-failed（失败），4-retrying（重试中）

### 6.3 站点类型说明
- `site_type`：0-cn（国内），1-us（美国），2-hk（香港），3-jp（日本），4-sg（新加坡）

### 6.4 账号类型说明
- `jimeng_account_type`：0-国内账号，1-国外账号

### 6.5 支持的模型
**图片模型**：
- `jimeng-4.5`（默认）
- `jimeng-4.1`
- `jimeng-4.0`
- `jimeng-3.1`
- `jimeng-3.0`
- `jimeng-2.1`
- `jimeng-xl-pro`
- `nanobanana`（仅国际站）
- `nanobananapro`（仅国际站）

**视频模型**：
- `jimeng-video-3.0-pro`（专业版）
- `jimeng-video-3.0`（标准版，默认）
- `jimeng-video-3.0-fast`（极速版，仅国内站）
- `jimeng-video-2.0-pro`（专业版v2）
- `jimeng-video-2.0`（标准版v2）

### 6.6 支持的宽高比
- 图片：`1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `3:2`, `2:3`, `21:9`
- 视频：`1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `21:9`

### 6.7 支持的分辨率
- 图片：`1k`, `2k`, `4k`
- 视频：`720p`, `1080p`

### 6.8 支持的视频时长
- `5`秒
- `10`秒

---

**文档版本**：v1.0  
**创建时间**：2025-01-16  
**最后更新**：2025-01-16

