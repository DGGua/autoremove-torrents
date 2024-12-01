import requests
from ..exception.connectionfailure import ConnectionFailure
from .. import logger

class HnrClient:
    def __init__(self, host, api_token, logger=None):
        self._host = host
        self._api_token = api_token
        self._logger = logger or logger.Logger.register(__name__)
        self._logger.info("初始化HNR客户端: %s" % host)
        
    def check_torrents(self, info_hashes):
        try:
            self._logger.info("准备查询%d个种子的HNR状态" % len(info_hashes))
            self._logger.debug("API地址: %s" % self._host)
            
            headers = {
                'Authorization': f'Bearer {self._api_token}',
                'Content-Type': 'application/json'
            }
            self._logger.debug("请求头: %s" % headers)
            
            # 将种子列表分批处理，每批50个
            batch_size = 50
            result = {}
            
            for i in range(0, len(info_hashes), batch_size):
                batch = info_hashes[i:i + batch_size]
                self._logger.info(f"处理第{i//batch_size + 1}批，共{len(batch)}个种子")
                
                data = {'info_hash': batch}
                self._logger.debug("请求数据: %s" % data)
                
                self._logger.info("发送API请求...")
                response = requests.post(
                    self._host,
                    headers=headers,
                    json=data
                )
                
                self._logger.info("API响应状态码: %d" % response.status_code)
                
                if response.status_code != 200:
                    error_msg = "HNR API请求失败: %s" % response.text
                    self._logger.error(error_msg)
                    raise ConnectionFailure(error_msg)
                    
                data = response.json()
                self._logger.debug("API响应数据: %s" % data)
                
                for record in data.get('data', []):
                    info_hash = record['torrent']['info_hash']
                    hnr_status_code = record['status']['hnr_status_code']
                    hnr_status = record['status']['hnr_status']
                    result[info_hash] = {
                        'hnr_status_code': hnr_status_code,
                        'hnr_status': hnr_status
                    }
                    self._logger.debug("种子 %s HNR状态码: %d (%s)" % (info_hash, hnr_status_code, hnr_status))
                    
            return result
            
        except Exception as e:
            error_msg = "连接HNR API失败: %s" % str(e)
            self._logger.error(error_msg)
            raise ConnectionFailure(error_msg) 