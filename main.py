
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interfaz import App


if __name__ == "__main__":
    app = App()
    app.mainloop()
