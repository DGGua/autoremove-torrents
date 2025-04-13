from .sortbase import ConditionWithSort

# FreeSpaceConditionBase:
# Implements basic deletion logic via free space
class FreeSpaceConditionBase(ConditionWithSort):
    def __init__(self, settings):
        ConditionWithSort.__init__(self, settings['action'])
        self._min = settings['min'] * (1 << 30) # Convert B to GiB

    def apply(self, free_space, torrents_to_remain, torrents_to_remove):
        torrents_to_remain = list(torrents_to_remain)
        torrents_to_remove = list(torrents_to_remove)
        ConditionWithSort.sort_torrents(self, torrents_to_remove)
        self.remove = set()
        self.remain = set(torrents_to_remain)
        for torrent in torrents_to_remove:
            if free_space < self._min:
                free_space += torrent.size
                self.remove.add(torrent)
            else:
                self.remain.add(torrent)
