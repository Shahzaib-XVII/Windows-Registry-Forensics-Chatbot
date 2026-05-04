import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(__file__))

from ui.main_window import launch

if __name__ == "__main__":
    launch()