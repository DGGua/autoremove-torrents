from .base import Condition
from .. import logger
import time
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

class CheckCondition(ABC):
    """检查条件的基类"""
    def __init__(self, config, logger):
        self._config = config
        self._logger = logger
        
    @abstractmethod
    def check(self, torrent, hnr_info=None):
        """检查条件是否满足
        
        Args:
            torrent: 种子对象
            hnr_info: HNR API 返回的信息（可选）
            
        Returns:
            tuple: (是否满足条件, 日志信息)
        """
        pass

class HnrStatusCondition(CheckCondition):
    """HNR 状态检查"""
    def check(self, torrent, hnr_info):
        target_codes = self._config.get('target_codes')
        if target_codes is None:
            return None, "未配置目标状态码，跳过检查"
            
        # 将单个状态码转换为列表
        if not isinstance(target_codes, list):
            target_codes = [target_codes]
            
        hnr_status_code = hnr_info['hnr_status_code']
        hnr_status = hnr_info['hnr_status']
        should_remove = hnr_status_code in target_codes
        
        log_msg = "当前状态码: %d (%s), 目标状态码: %s, 是否匹配: %s" % (
            hnr_status_code,
            hnr_status,
            target_codes,
            "是" if should_remove else "否"
        )
        
        return should_remove, log_msg

class LastActivityCondition(CheckCondition):
    """最后活动时间检查"""
    def check(self, torrent, hnr_info=None):
        last_activity = self._config.get('last_activity')
        if not last_activity:
            return None, "未配置最后活动时间限制"
            
        if not hasattr(torrent, 'last_activity') or torrent.last_activity is None:
            return None, "种子没有最后活动时间记录"
            
        inactive_seconds = torrent.last_activity
        inactive_hours = inactive_seconds / 3600
        inactive_days = inactive_hours / 24
        should_remove = inactive_seconds >= last_activity
        
        log_msg = "不活跃时长: %.1f小时 (%.1f天), 设定限制: %.1f小时 (%.1f天), 是否超时: %s" % (
            inactive_hours,
            inactive_days,
            last_activity / 3600,
            last_activity / 86400,
            "是" if should_remove else "否"
        )
        
        return should_remove, log_msg

class SeedTimeCondition(CheckCondition):
    """做种时间检查"""
    def check(self, torrent, hnr_info=None):
        min_seed_time = self._config.get('min_seed_time')
        if not min_seed_time:
            return None, "未配置最小做种时间"
            
        if not hasattr(torrent, 'seeding_time') or torrent.seeding_time is None:
            return None, "种子没有做种时间记录"
            
        seed_hours = torrent.seeding_time / 3600
        seed_days = seed_hours / 24
        should_remove = torrent.seeding_time >= min_seed_time
        
        log_msg = "已做种: %.1f小时 (%.1f天), 设定限制: %.1f小时 (%.1f天), 是否达标: %s" % (
            seed_hours,
            seed_days,
            min_seed_time / 3600,
            min_seed_time / 86400,
            "是" if should_remove else "否"
        )
        
        return should_remove, log_msg

class UploadSpeedCondition(CheckCondition):
    """当前上传速度检查"""
    def check(self, torrent, hnr_info=None):
        min_upload_speed = self._config.get('min_upload_speed')
        if not min_upload_speed:
            return None, "未配置最小上传速度"
            
        if not hasattr(torrent, 'upload_speed') or torrent.upload_speed is None:
            return None, "种子没有上传速度记录"
            
        speed_kb = torrent.upload_speed / 1024
        speed_mb = speed_kb / 1024
        should_remove = torrent.upload_speed <= min_upload_speed
        
        log_msg = "当前上传速度: %.2fMB/s (%.2fKB/s), 设定限制: %.2fKB/s, 是否过低: %s" % (
            speed_mb,
            speed_kb,
            min_upload_speed / 1024,
            "是" if should_remove else "否"
        )
        
        return should_remove, log_msg

class RatioCondition(CheckCondition):
    """分享率检查"""
    def check(self, torrent, hnr_info=None):
        min_ratio = self._config.get('min_ratio')
        if not min_ratio:
            return None, "未配置最小分享率"
            
        if not hasattr(torrent, 'uploaded') or not hasattr(torrent, 'downloaded'):
            return None, "种子没有上传/下载量记录"
            
        if torrent.downloaded == 0:
            return None, "种子未产生下载量"
            
        ratio = torrent.uploaded / torrent.downloaded
        should_remove = ratio >= min_ratio
        
        log_msg = "当前分享率: %.2f, 设定限制: %.2f, 是否达标: %s" % (
            ratio,
            min_ratio,
            "是" if should_remove else "否"
        )
        
        return should_remove, log_msg

class HnrCondition(Condition):
    """HNR 条件主类"""
    def __init__(self, client, config, strategy_name=None, logger=None):
        self._client = client
        self._config = config
        self._strategy_name = strategy_name or "HNR条件"
        self._logger = logger or logger.Logger.register(__name__)
        
        # 初始化所有检查条件
        self._conditions = {
            'status': HnrStatusCondition(config, self._logger),
            'last_activity': LastActivityCondition(config, self._logger),
            'seed_time': SeedTimeCondition(config, self._logger),
            'upload_speed': UploadSpeedCondition(config, self._logger),
            'ratio': RatioCondition(config, self._logger)
        }
        
        # 条件显示名称映射
        self._condition_names = {
            'status': 'HNR状态',
            'last_activity': '最后活动',
            'seed_time': '做种时间',
            'upload_speed': '上传速度',
            'ratio': '分享率'
        }
        
        self._logger.debug("初始化%s，配置: %s" % (self._strategy_name, config))
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
        
        try:
            self._logger.debug("正在获取种子信息...")
            api_results = self._client.check_torrents(info_hashes)
            
            self.remain = set()
            self.remove = set()
            
            # 处理每个种子
            for torrent in torrents:
                self._logger.debug("========================================")
                self._logger.debug("处理种子: %s (%s)" % (torrent.name, torrent.hash))
                
                if torrent.hash not in api_results:
                    self._logger.debug("种子未在API响应中找到，跳过检查")
                    self.remain.add(torrent)
                    continue
                
                hnr_info = api_results[torrent.hash]
                hnr_status_code = hnr_info['hnr_status_code']
                hnr_status = hnr_info['hnr_status']
                self._logger.debug("HNR状态码: %d (%s)" % (hnr_status_code, hnr_status))
                
                # 检查所有条件
                should_remove = True
                check_results = []  # 存储所有条件的检查结果
                
                # 先检查状态码
                status_result, status_log = self._conditions['status'].check(torrent, hnr_info)
                check_results.append(("status", status_result, status_log))
                if status_result is None or not status_result:
                    should_remove = False
                
                # 如果状态码匹配，继续检查其他条件
                if should_remove:
                    for name, condition in self._conditions.items():
                        if name == 'status':
                            continue
                            
                        result, log_msg = condition.check(torrent, hnr_info)
                        check_results.append((name, result, log_msg))
                        # 只有当结果不为 None 时才参与条件判断
                        if result is not None:
                            should_remove = should_remove and result
                
                # 输出所有检查结果
                self._logger.debug("条件检查结果:")
                for condition_name, result, log_msg in check_results:
                    status = "跳过" if result is None else ("删除" if result else "不删")
                    self._logger.debug("[%s] %s -> %s" % (
                        self._condition_names[condition_name],
                        log_msg,
                        status
                    ))
                self._logger.debug("最终决定: %s" % ("删除" if should_remove else "保留"))
                self._logger.debug("========================================")
                
                if should_remove:
                    self.remove.add(torrent)
                else:
                    self.remain.add(torrent)
                    
            self._logger.info("%s - 处理完成 - 保留: %d个, 删除: %d个" % (
                self._strategy_name,
                len(self.remain),
                len(self.remove)
            ))
            
        except Exception as e:
            self._logger.error("HNR检查过程中发生错误: %s" % str(e))
            self.remain = set(torrents)
            self.remove = set()