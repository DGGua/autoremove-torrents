from .base import Condition
from .. import logger

class HnrCondition(Condition):
    def __init__(self, client, require_complete=True, logger=None):
        self._client = client
        self._require_complete = require_complete
        self._logger = logger or logger.Logger.register(__name__)
        self._logger.debug("初始化HNR条件，require_complete=%s" % require_complete)
        self.remain = set()
        self.remove = set()
        
    def apply(self, client_status, torrents):
        if not torrents:
            self._logger.debug("没有种子需要检查")
            self.remain = set()
            self.remove = set()
            return
            
        info_hashes = [torrent.hash for torrent in torrents]
        self._logger.debug("开始检查%d个种子的HNR状态" % len(info_hashes))
        self._logger.debug("种子hash列表: %s" % info_hashes)
        
        try:
            self._logger.debug("正在请求HNR API...")
            hnr_status = self._client.check_torrents(info_hashes)
            self._logger.debug("获取到HNR状态: %s" % hnr_status)
            
            self.remain = set()
            self.remove = set()
            
            # 只处理在API响应中存在的种子
            for torrent in torrents:
                if torrent.hash not in hnr_status:
                    self._logger.debug(
                        "种子 %s (%s) - 未在API响应中找到，跳过检查" % (
                            torrent.name,
                            torrent.hash
                        )
                    )
                    self.remain.add(torrent)
                    continue
                    
                is_complete = hnr_status[torrent.hash]
                should_remove = is_complete == self._require_complete
                self._logger.debug(
                    "种子 %s (%s) - HNR状态: %s, 是否删除: %s" % (
                        torrent.name,
                        torrent.hash,
                        "已达标" if is_complete else "未达标",
                        "是" if should_remove else "否"
                    )
                )
                if should_remove:
                    self.remove.add(torrent)
                else:
                    self.remain.add(torrent)
                    
            self._logger.info("处理完成 - 保留: %d个, 删除: %d个" % (len(self.remain), len(self.remove)))
            
        except Exception as e:
            self._logger.error("HNR检查过程中发生错误: %s" % str(e))
            self.remain = set(torrents)
            self.remove = set()