"""
应用配置——集中管理路径、端口等可调参数。

把配置抽成单独文件，而不是散落在各处硬编码，好处是：
  1. 改配置只动一个文件
  2. 部署到不同环境（本地开发 / 生产服务器）时只改这里
"""
from pathlib import Path
import os
# dotenv：从 .env 文件加载环境变量。
# .env 文件放敏感配置（如 API key），不进 git（已 gitignore）。
# load_dotenv() 会在启动时读取 backend/.env，把里面的 KEY=VALUE 注入 os.environ，
# 之后 os.environ.get("DEEPSEEK_API_KEY") 就能拿到值。
# 必须在 import 其他模块之前调用，确保环境变量先加载。
from dotenv import load_dotenv

# BASE_DIR 指向 backend/ 目录。
# __file__ 是当前文件（config.py）的路径，在 app/ 目录里。
# .resolve().parent 拿到 app/，再 .parent 拿到 backend/。
# 用 Path 而非字符串拼接，自动处理跨平台路径分隔符（macOS/Linux 用 /，Windows 用 \）。
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件（路径：backend/.env）。
# .env 文件不存在时不报错，静默跳过——这样没配 key 也能启动后端（只是流水线 LLM 步骤会报错）。
load_dotenv(BASE_DIR / ".env")


class settings:
    """集中存放所有配置项。

    这里用普通类而非 dataclass / Pydantic Settings，是为了 Phase 0 极简。
    Phase 4 部署时可换成 pydantic-settings 从环境变量读取（比如生产环境改 DB 路径）。
    """

    # SQLite 数据库文件路径。放在 backend/data/kb.db，data/ 目录已 gitignore。
    # 运行时 database.py 会自动创建 data/ 目录，不用手动建。
    db_path = BASE_DIR / "data" / "kb.db"

    # CORS（跨域资源共享）允许的前端来源。
    # 从环境变量读，逗号分隔。本地开发不配则用默认值。
    # .env 里写：CORS_ORIGINS=http://localhost:5173  或  http://你的公网IP
    _cors_env = os.environ.get("CORS_ORIGINS", "")
    if _cors_env:
        cors_origins = [o.strip() for o in _cors_env.split(",")]
    else:
        cors_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
