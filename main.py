# 终极修复版 main.py
import sys
import os

# 强行把所有路径都加上
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "src"))

# 直接导入，不写 src.
from gui_app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()