# H&R 考核记录查询 API

## 接口说明
查询用户的 H&R (Hit and Run) 考核记录

## 请求信息
- 请求方法: POST
- 请求URL: `https://tjupt.org/api/v1/hnr.php`
- 需要认证: 是 (需要在请求头中携带 API Token，在 [PT控制面板](https://tjupt.org/usercp.php?action=user_api_token) 获取API Token)

### 请求头 Headers
```
Authorization: Bearer YOUR_API_TOKEN 或者 X-Api-Key: YOUR_API_TOKEN
Content-Type: application/json
```

### 请求参数 Body
#### 方式一：按种子info_hash查询
```json
{
    "info_hash": [
        "914eaa7b36b79fd35e836bdad1bb6dbf0d2cd601",
        "42cf9bd10006721d61418a879fb2f480e1e073c2"
    ]
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| info_hash | array | 是 | 种子的info_hash数组，每个hash为40位16进制字符串，最多支持50个 |

#### 方式二：按考核状态查询
```json
{
    "status": "ongoing",
    "page": 1,
    "per_page": 50,
    "sort": "-id",
    "active": "no"  // 可选参数
}
```

| 参数       | 类型      | 必填  | 说明                   |
| -------- | ------- | --- | -------------------- |
| status   | string  | 否   | 考核状态，默认值：ongoing     |
| page     | integer | 否   | 页码，默认值：1             |
| per_page | integer | 否   | 每页记录数，默认值：50，最大值：100 |
| sort     | string  | 否   | 排序方式，默认值：-id (id降序)  |
| active   | string  | 否   | 是否正在做种/下载，可选值：yes/no |

| status可选值  | 说明    |
| ---------- | ----- |
| speedup    | 加速区种子 |
| unstarted  | 未开始   |
| waiting    | 等待中   |
| ongoing    | 考核中   |
| unfinished | 未达标   |
| complete   | 已达标   |
| makeup     | 后达标   |

| sort可选值         | 说明       |
| --------------- | -------- |
| id              | id升序     |
| added_at        | 添加时间升序   |
| updated_at      | 更新时间升序   |
| hnr_started_at  | 考核开始时间升序 |
| -id             | id降序     |
| -added_at       | 添加时间降序   |
| -updated_at     | 更新时间降序   |
| -hnr_started_at | 考核开始时间降序 |

## 响应信息

### 成功响应
#### 按info_hash查询
```json
{
    "meta": {
        "total": 1,
        "filters": {
            "info_hash": [
                "914eaa7b36b79fd35e836bdad1bb6dbf0d2cd601"
            ]
        }
    },
    "data": [
        {
            "id": 12345,
            "torrent": {
                "tid": 67890,
                "name": "种子主标题",
                "sub_name": "种子副标题",
                "size": 1073741824,
                "info_hash": "914eaa7b36b79fd35e836bdad1bb6dbf0d2cd601"
            },
            "status": {
                "seed_status": "inactive",
                "hnr_status_code": 20,
                "hnr_status": "已达标",
                "hnr_score": 5,
                "need_seed_time": 86400,
                "extend_the_deadline": 0,
                "speedup_bonus": -1.0
            },
            "statistics": {
                "uploaded": 0,
                "downloaded": 4267063771,
                "seed_time": 92670,
                "leech_time": 0,
                "ratio": 0,
                "progress": 100
            },
            "timestamps": {
                "added_at": "2021-08-13 19:50:37",
                "updated_at": "2021-08-17 16:10:10",
                "hnr_started_at": "2021-08-13 20:38:49",
                "ten_percent_at": "2021-08-13 20:17:29"
            }
        }
    ]
}
```

| hnr_status_code | 类型      | hnr_status |
| --------------- | ------- | ---------- |
| 0               | integer | 未触发        |
| 1               | integer | 24h等待期     |
| 5               | integer | 下载考核中      |
| 6               | integer | 下载考核中(过半)  |
| 10              | integer | 做种考核中      |
| 11              | integer | 做种考核中(过半)  |
| 12              | integer | 未达标        |
| 20              | integer | 已达标        |
| 21              | integer | 后达标        |
| 40              | integer | 种子被删取消     |
| 41              | integer | 未成功下载取消    |
| 42              | integer | 管理员取消      |
| 43              | integer | 自行放弃       |
| 44              | integer | 冗余考核       |

| speedup_bonus | 类型    | 说明        |
| ------------- | ----- | --------- |
| -3.0          | float | 加速未成功     |
| -2.0          | float | 未获得加速奖励   |
| -1.0          | float | 加速奖励待结算   |
| 0.0           | float | 非加速种子     |
| >0.0          | float | 获得的具体奖励数值 |

#### 按状态查询
```json
{
    "meta": {
        "total": 100,
        "per_page": 25,
        "current_page": 1,
        "last_page": 4,
        "filters": {
            "status": "ongoing",
            "page": 1,
            "per_page": 25,
            "sort": "-id"
        }
    },
    "data": [...]
}
```

### 错误响应
```json
{
    "error": true,
    "message": "info_hash must be an array"
}
```

常见错误:
- 400: 请求参数错误
- 401: 缺少API Token或Token无效
- 405: 请求方式错误

## 注意事项
1. 需要先开启两步验证(2FA)才能使用API功能
2. API Token有效期为3个月
3. 单次请求最多查询50个info_hash
4. 查询结果会缓存10分钟