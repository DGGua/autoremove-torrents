from .base import Condition
from .. import logger
import time
from datetime import datetime, timedelta

class HnrCondition(Condition):
    def __init__(self, client, config, logger=None):
        self._client = client
        self._require_complete = config.get('require_complete', True)
        self._last_activity = config.get('last_activity')
        self._logger = logger or logger.Logger.register(__name__)
        self._logger.debug("初始化HNR条件，require_complete=%s, last_activity=%.1f小时" % (
            self._require_complete, 
            (self._last_activity if self._last_activity else 0) / 3600
        ))
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
            current_time = time.time()
            
            # 只处理在API响应中存在的种子
            for torrent in torrents:
                self._logger.debug("----------------------------------------")
                self._logger.debug("处理种子: %s (%s)" % (torrent.name, torrent.hash))
                
                # 检查 last_activity 是否为有效值
                if not hasattr(torrent, 'last_activity') or torrent.last_activity is None:
                    self._logger.debug("种子没有最后活动时间记录，跳过检查")
                    self.remain.add(torrent)
                    continue
                    
                # 记录不活跃时长
                inactive_seconds = torrent.last_activity
                inactive_hours = inactive_seconds / 3600
                inactive_days = inactive_hours / 24
                
                self._logger.debug("已经不活跃: %.1f小时 (%.1f天)" % (inactive_hours, inactive_days))
                
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
                should_remove_hnr = is_complete == self._require_complete
                self._logger.debug("HNR状态: %s, 是否符合删除条件: %s" % (
                    "已达标" if is_complete else "未达标",
                    "是" if should_remove_hnr else "否"
                ))
                
                # 检查最后活动时间
                should_remove_activity = False
                if self._last_activity is not None:
                    should_remove_activity = inactive_seconds >= self._last_activity
                    self._logger.debug(
                        "不活跃时长: %.1f小时 (%.1f天), 设定限制: %.1f小时 (%.1f天), 是否超时: %s" % (
                            inactive_hours,
                            inactive_days,
                            self._last_activity / 3600,
                            self._last_activity / 86400,
                            "是" if should_remove_activity else "否"
                        )
                    )
                
                # 取两个条件的交集
                should_remove = should_remove_hnr and (should_remove_activity if self._last_activity is not None else True)
                
                self._logger.debug(
                    "最终决定 - HNR状态: %s, 活动状态: %s, 是否删除: %s" % (
                        "已达标" if is_complete else "未达标",
                        "超时" if should_remove_activity else "活跃",
                        "是" if should_remove else "否"
                    )
                )
                
                if should_remove:
                    self.remove.add(torrent)
                else:
                    self.remain.add(torrent)
                    
            self._logger.info("处理完成 - HNR条件下 保留: %d个, 删除: %d个" % (len(self.remain), len(self.remove)))
            
        except Exception as e:
            self._logger.error("HNR检查过程中发生错误: %s" % str(e))
            self.remain = set(torrents)
            self.remove = set()