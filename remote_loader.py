import os
import sys
import importlib
import subprocess
from git import Repo, GitCommandError

# ================= ⚙️ 配置区 =================
REMOTE_REPO_URL = "https://github.com/Tenghue/Facai.git"
LOCAL_REPO_DIR = "./_git_cache"       # 本地缓存目录
MODULE_NAME = "百十个定位_体"       # 远程仓库中的 .py 文件名（不带 .py）
AUTO_INSTALL_DEPS = True              # 是否自动安装远程仓库的 requirements.txt
# =============================================

def load_remote_module(force_update: bool = False):
    """
    自动从远程 Git 仓库拉取最新代码并返回模块对象
    
    Args:
        force_update: True=强制拉取最新代码; False=优先使用本地缓存(仅首次克隆)
    Returns:
        module: 成功返回模块对象，失败返回 None
    """
    try:
        # 1. 克隆或更新仓库
        if not os.path.exists(LOCAL_REPO_DIR):
            print(f"📥 首次运行，正在克隆远程模块...")
            Repo.clone_from(REMOTE_REPO_URL, LOCAL_REPO_DIR)
        elif force_update:
            print(f"🔄 正在拉取远程模块最新代码...")
            repo = Repo(LOCAL_REPO_DIR)
            repo.remotes.origin.pull()
        else:
            print(f"✅ 使用本地缓存模块 (传入 force_update=True 可强制更新)")

        # 2. 自动安装依赖（可选）
        if AUTO_INSTALL_DEPS:
            req_path = os.path.join(LOCAL_REPO_DIR, "requirements.txt")
            if os.path.exists(req_path):
                print(f"📦 检测到 requirements.txt，正在同步依赖...")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", req_path, "-q"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

        # 3. 注入路径并动态加载/重载模块
        abs_local_dir = os.path.abspath(LOCAL_REPO_DIR)
        if abs_local_dir not in sys.path:
            sys.path.insert(0, abs_local_dir)

        if MODULE_NAME in sys.modules:
            module = importlib.reload(sys.modules[MODULE_NAME])
        else:
            module = importlib.import_module(MODULE_NAME)

        print(f"🎯 远程模块 [{MODULE_NAME}] 加载成功!")
        return module

    except GitCommandError as e:
        print(f"❌ Git 操作失败 (网络/权限/地址错误): {e}")
    except ImportError as e:
        print(f"❌ 模块导入失败 (文件名或路径不正确): {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
    
    return None