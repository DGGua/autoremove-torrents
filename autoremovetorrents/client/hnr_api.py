import requests
from ..exception.connectionfailure import ConnectionFailure
from .. import logger

class HnrClient:
    def __init__(self, host, api_token, logger=None):
        self._host = host
        self._api_token = api_token
        self._logger = logger or logger.Logger.register(__name__)
        self._logger.debug("初始化HNR客户端: %s" % host)
        
    def check_torrents(self, info_hashes):
        try:
            self._logger.debug("准备查询%d个种子的HNR状态" % len(info_hashes))
            self._logger.debug("API地址: %s" % self._host)
            
            headers = {
                'Authorization': f'Bearer {self._api_token}',
                'Content-Type': 'application/json'
            }
            self._logger.debug("请求头: %s" % headers)
            
            data = {'info_hash': info_hashes}
            self._logger.debug("请求数据: %s" % data)
            
            self._logger.debug("发送API请求...")
            response = requests.post(
                self._host,
                headers=headers,
                json=data
            )
            
            self._logger.debug("API响应状态码: %d" % response.status_code)
            
            if response.status_code != 200:
                error_msg = "HNR API请求失败: %s" % response.text
                self._logger.error(error_msg)
                raise ConnectionFailure(error_msg)
                
            result = {}
            data = response.json()
            self._logger.debug("API响应数据: %s" % data)
            
            for record in data.get('data', []):
                info_hash = record['torrent']['info_hash']
                is_complete = record['status']['hnr_status_code'] in [20, 21]
                result[info_hash] = is_complete
                self._logger.debug(
                    "种子 %s HNR状态: %s (状态码: %s)" % (
                        info_hash,
                        "已达标" if is_complete else "未达标",
                        record['status']['hnr_status_code']
                    )
                )
                
            return result
            
        except Exception as e:
            error_msg = "连接HNR API失败: %s" % str(e)
            self._logger.error(error_msg)
            raise ConnectionFailure(error_msg) 