import tkinter as tk
from gui.game_gui import GameGUI


def main():
    """Entry point for the Tic-Tac-Toe application."""
    root = tk.Tk()
    GameGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
