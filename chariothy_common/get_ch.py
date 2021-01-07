from .utils import is_win, is_linux, is_macos

class GetCh:
    """Gets a single character from standard input.  Does not echo to the screen.
       Ex. getch = GetCh()
           ch = getch()
    """
    def __init__(self):
        if is_win():
            self.impl = _GetchWindows()
        elif is_linux():
            self.impl = _GetchUnix()
        elif is_macos():
            # Patch for MACOS for now
            self.impl = lambda : input()

    def __call__(self): return str(self.impl())


class _GetchUnix:
    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __call__(self):
        import msvcrt
        return str(msvcrt.getch(), encoding='utf-8')
