"""
数据库引擎 + 会话管理。

核心概念：
  - engine：和数据库的"连接池"，全局只建一个，所有请求复用。
  - Session：一次数据库操作的"工作单元"，处理完一个请求就关闭。
  - get_session：FastAPI 依赖注入用的生成器，每个请求自动开一个 session 用完自动关。
"""
from sqlmodel import create_engine, Session, SQLModel

from .config import settings
# 导入 Paper 是为了"触发模型注册"——
# SQLModel.metadata.create_all 需要先知道有哪些表，而表定义在 Paper 类里。
# import 语句会让 Python 执行 Paper 类体，从而把 Paper 注册到 SQLModel.metadata。
# 看起来没用，删掉会导致建表时 metadata 是空的，papers 表建不出来。
from .models.paper import Paper  # noqa: F401  （noqa 抑制"未使用导入"警告）


# create_engine 创建数据库引擎。
# f"sqlite:///{db_path}"：SQLAlchemy 的连接字符串格式，sqlite:/// 是协议前缀，后面跟文件路径。
#   - 相对内存数据库：sqlite:// （不持久化，测试用）
#   - 相对文件库：sqlite:///path/to/db.db （持久化到文件）
#
# connect_args={"check_same_thread": False}：
#   SQLite 默认只允许"创建连接的线程"使用它（check_same_thread=True）。
#   但 FastAPI 用线程池处理并发请求，不同请求可能来自不同线程。
#   设成 False 允许跨线程共享连接，否则并发请求会报 "SQLite objects created in a thread
#   can only be used in that same thread" 错误。
engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
    echo=False,   # echo=True 会打印所有 SQL 到控制台，调试时打开看实际执行的 SQL
)


def create_db_and_tables():
    """
    作用：创建 data/ 目录（如果不存在）并建表。

    幂等操作：表已存在则跳过，不会报错也不会覆盖数据。
    在 main.py 的 lifespan 钩子里调用——应用启动时自动建表。

    注意：这只建表，不处理 schema 变更。
    Phase 0 改了模型字段后，删掉 backend/data/kb.db 重启即可重建（数据都是手插种子，丢了无所谓）。
    Phase 2 有真实数据后再上 Alembic 做增量迁移。
    """
    # 确保父目录存在（backend/data/），不存在则递归创建，已存在不报错。
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    # create_all 扫描所有已注册的 SQLModel 模型，生成 CREATE TABLE 语句执行。
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    作用：FastAPI 依赖注入用的数据库会话生成器。

    返回：生成器，yield 一个 Session 对象。

    使用场景：
        在路由函数里写 `session: Session = Depends(get_session)`，
        FastAPI 收到请求时自动调用 get_session()，把 yield 出来的 Session 传给路由函数；
        请求处理完后（路由函数返回），自动执行 yield 后面的代码关闭 session。

    这是 FastAPI 的依赖注入（Dependency Injection）机制：
        传统写法要在函数里手动 session = Session(engine) ... session.close()，
        容易忘记关闭导致连接泄漏。用 Depends 把"开/关 session"的逻辑抽到一处，
        路由函数只管"用"，不用关心生命周期。

    用 yield 而非 return 的原因：
        yield 让函数变成生成器，FastAPI 能在"请求结束后"继续执行 yield 之后的代码
        （这里是 with 块的退出，自动 close）。return 的话函数就结束了，没法善后。
    """
    # with 语句保证无论请求处理是否抛异常，session 都会被正确关闭。
    with Session(engine) as session:
        yield session
