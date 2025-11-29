### 一次性设置（初始配置）

#### 1. 安装 Alembic

```bash
pip install alembic
```

#### 2. 初始化 Alembic

在项目根目录（有 `main.py` 的地方）执行：

```bash
alembic init alembic
```

这会生成一个 `alembic/` 文件夹和 `alembic.ini` 配置文件。

---

### 修改 Alembic 配置

#### 3. 在 `alembic.ini` 中配置数据库连接

找到：

```ini
sqlalchemy.url = sqlite:///./test.db
```

改成你的数据库地址，例如：

```ini
sqlalchemy.url = mysql+pymysql://root:123456@localhost:3306/your_db_name
```

>  确保你数据库已创建，否则后续操作会报错。

#### 4. 修改 `alembic/env.py` 文件，引入你的 `Base`

找到这几行：

```python
from myapp import mymodel  # this is a placeholder
target_metadata = mymodel.Base.metadata
```

改为你自己的，比如：

```python
from app.models.base import Base
target_metadata = Base.metadata
```

或者，如果你用了 `models.__init__.py` 聚合：

```python
from app.models import Base
target_metadata = Base.metadata
```

---

### 生成并应用迁移文件

#### 5. 生成迁移脚本（Autogenerate）

```bash
alembic revision --autogenerate -m "auto update"
```

这一步会自动检测你的 models 中定义的表结构，生成一个迁移脚本（在 `alembic/versions/` 目录下）。

 检查生成的脚本，确认 SQL 是你期望的。

#### 6. 执行迁移，生成表结构

```bash
alembic upgrade head
```

执行成功后，MySQL 中就会出现你定义的表了。

---

### 开发阶段常用操作速查

| 操作             | 命令                                       |
| ---------------- | ------------------------------------------ |
| 初始化 Alembic   | `alembic init alembic`                     |
| 生成迁移脚本     | `alembic revision --autogenerate -m "xxx"` |
| 应用最新迁移     | `alembic upgrade head`                     |
| 回滚上一次迁移   | `alembic downgrade -1`                     |
| 查看当前迁移版本 | `alembic current`                          |

---

### 示例数据库地址格式（MySQL）

```text
mysql+pymysql://root:123456@localhost:3306/your_db_name
mysql+asyncmy
```

确保你已经安装 `pymysql`：

```bash
pip install pymysql
```

---

## 修改建议

### 原来的 `models/__init__.py`：

```python
from .base import *
from .user import *
```

### 改成自动导入（推荐）：



~~~python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
~~~

```python
from .base import Base
import importlib
import pathlib

# 自动导入当前目录下所有模型文件（除了 base.py 和 __init__.py）
model_dir = pathlib.Path(__file__).parent
for file in model_dir.glob("*.py"):
    if file.name not in ("__init__.py", "base.py") and file.suffix == ".py":
        module_name = f"{__name__}.{file.stem}"
        importlib.import_module(module_name)

__all__ = ["Base"]
```

这样以后你新增 `models/article.py`、`models/order.py`，根本不需要再改 `__init__.py`，Alembic 也能正确发现它们。

---

## `env.py` 保持这样即可：

```python
from app.models import Base

target_metadata = Base.metadata
```

---

这种方式等同 Django 的 `apps.py` 中 `auto-discover` 模型，**更现代、企业级**，也能让团队开发更顺滑。

