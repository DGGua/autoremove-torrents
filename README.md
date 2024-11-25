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

API 接口文档：[hnr_api.md](https://github.com/tjupt/autoremove-torrents/blob/master/hnr_api.md)

在策略配置中添加 `hnr` 部分：

- `host`: hnr API 地址
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

## 许可证

MIT License