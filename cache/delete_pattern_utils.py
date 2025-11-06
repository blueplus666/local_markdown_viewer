"""
缓存键通配删除工具。

场景：
- 缓存实现不原生支持 delete_pattern 时，按通配符（glob）批量删除键
- 例如第8章中链接分辨缓存需要按 "link_resolution:<hash>:*" 失效

使用示例：

```python
from cache.delete_pattern_utils import delete_pattern

# 假设 cache 对象实现了 keys() 与 delete(key)
pattern = "link_resolution:abc123:*"
removed = delete_pattern(cache, pattern)
print(f"Removed {removed} keys")
```
"""
import fnmatch
from typing import Protocol


class CacheProtocol(Protocol):
    """约束 minimal cache 接口，避免强依赖具体实现。"""
    def keys(self): ...
    def delete(self, key: str): ...


def delete_pattern(cache: CacheProtocol, pattern: str) -> int:
    """按 glob 样式 pattern 删除缓存键，返回删除数量。"""
    keys_to_delete = [k for k in list(cache.keys()) if fnmatch.fnmatch(k, pattern)]
    for k in keys_to_delete:
        cache.delete(k)
    return len(keys_to_delete)