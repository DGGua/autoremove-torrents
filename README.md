# Auto Remove Torrents (H&R Version)

这是一个支持 H&R 检查的自动删种程序，基于 [autoremove-torrents](https://github.com/jerrymakesjelly/autoremove-torrents) 修改，在此感谢原作者jerrymakesjelly。

## 新增功能

- 支持通过 API 检查种子的 H&R 状态
- 可以根据 H&R 达标情况决定是否删除种子

## 安装

```bash
pip install autoremove-torrents-hnr
```

## 配置示例

```yaml
my_task:
  client: qbittorrent
  host: http://127.0.0.1:7474
  username: admin
  password: password
  
  strategies:
    remove_completed_hnr:
      categories: 
        - TJUPT
      hnr:
        host: https://pt.example.org/api/v1/hnr.php
        api_token: your_api_token
        require_complete: true  # true表示只删除已达标的种子
```

其他条件配置请参考原项目 [autoremove-torrents](https://github.com/jerrymakesjelly/autoremove-torrents) 的文档。

## hnr 配置说明

H&R API 接口文档：[hnr_api.md](https://github.com/tjupt/autoremove-torrents/blob/master/hnr_api.md)

在策略配置中添加 `hnr` 部分：

- `host`: H&R API 地址
- `api_token`: API 访问令牌
- `require_complete`: 
  - `true`: 只删除 H&R 已达标的种子
  - `false`: 只删除 H&R 未达标的种子

## 使用方法

```bash
# 预览模式（不会真正删除）
autoremove-torrents --view --conf=config.yml

# 正常运行
autoremove-torrents --conf=config.yml
```

## 日志

```bash
autoremove-torrents --conf=config.yml --log=logs/autoremove.log
```

## 项目结构
### 1 客户端模块 (client/)
- hnr_api.py: H&R API 客户端，用于查询种子的 H&R 状态
- 其他客户端适配器（如 qBittorrent, Transmission 等）
### 2 条件模块 (condition/)
- base.py: 条件基类，定义了条件的基本接口
- hnr.py: H&R 条件检查实现
- 其他条件实现（如分享率、做种时间等）
### 3 核心功能文件
- strategy.py: 策略执行器，负责：
- 应用各种条件
- 管理种子的保留和删除列表
- 执行删除操作

- conditionparser.py: 条件解析器，负责：
- 解析配置文件中的条件
- 创建对应的条件实例
- 处理条件组合

## 工作流程
### 1 配置加载
- 读取 config.yml
- 解析任务和策略配置
### 2 客户端连接
- 根据配置创建对应的客户端实例
- 建立连接并验证
### 3 策略执行
- 获取种子列表
- 应用分类过滤
- 执行条件检查
- 确定删除列表
### 4 删除操作
- 执行种子删除
- 记录操作日志

## 许可证

MIT License