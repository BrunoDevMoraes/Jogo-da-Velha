"""Entry point for the Tic-Tac-Toe application."""

import customtkinter as ctk
from gui.game_gui import GameGUI


def main():
    """Entry point for the Tic-Tac-Toe application."""
    root = ctk.CTk()
    GameGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
