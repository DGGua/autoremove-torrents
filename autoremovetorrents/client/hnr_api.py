import requests
from ..exception.connectionfailure import ConnectionFailure
from .. import logger

class HnrClient:
    # 类级别的缓存字典，所有实例共享
    _response_cache = {}
    
    def __init__(self, host, api_token, logger=None):
        self._host = host
        self._api_token = api_token
        self._logger = logger or logger.Logger.register(__name__)
        self._logger.info("初始化HNR客户端: %s" % host)
        
    def check_torrents(self, info_hashes):
        try:
            self._logger.info("准备查询%d个种子的HNR状态" % len(info_hashes))
            self._logger.debug("API地址: %s" % self._host)
            
            # 过滤出未缓存的种子
            uncached_hashes = [h for h in info_hashes if h not in self._response_cache]
            
            if uncached_hashes:
                self._logger.info("发现%d个本地未缓存的种子，准备请求API" % len(uncached_hashes))
                
                headers = {
                    'Authorization': f'Bearer {self._api_token}',
                    'Content-Type': 'application/json'
                }
                
                # 将种子列表分批处理，每批50个
                batch_size = 50
                
                for i in range(0, len(uncached_hashes), batch_size):
                    batch = uncached_hashes[i:i + batch_size]
                    self._logger.info(f"处理第{i//batch_size + 1}批，共{len(batch)}个种子")
                    
                    data = {'info_hash': batch}
                    
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
                    
                    # 更新缓存
                    for record in data.get('data', []):
                        info_hash = record['torrent']['info_hash']
                        hnr_status_code = record['status']['hnr_status_code']
                        hnr_status = record['status']['hnr_status']
                        self._response_cache[info_hash] = {
                            'hnr_status_code': hnr_status_code,
                            'hnr_status': hnr_status
                        }
                        self._logger.debug("从远端API获取种子 %s HNR状态码: %d (%s)" % (info_hash, hnr_status_code, hnr_status))
            else:
                self._logger.info("所有种子状态均已本地缓存，无需请求API")
            
            # 从缓存中获取所有请求的种子状态
            result = {}
            for info_hash in info_hashes:
                if info_hash in self._response_cache:
                    result[info_hash] = self._response_cache[info_hash]
                    # self._logger.debug("从本地缓存获取种子 %s HNR状态码: %d (%s)" % (
                    #     info_hash,
                    #     result[info_hash]['hnr_status_code'],
                    #     result[info_hash]['hnr_status']
                    # ))
                    
            return result
            
        except Exception as e:
            error_msg = "连接HNR API失败: %s" % str(e)
            self._logger.error(error_msg)
            raise ConnectionFailure(error_msg)
            
    @classmethod
    def clear_cache(cls):
        """清除响应缓存"""
        cls._response_cache.clear() 