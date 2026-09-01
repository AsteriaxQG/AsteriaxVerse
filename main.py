"""Asteriax Verse application entry point."""

from __future__ import annotations

import sys
import traceback


def main() -> int:
    from core.updater import run_update_bootstrap

    bootstrap_result = run_update_bootstrap()
    if bootstrap_result is not None:
        return bootstrap_result
    try:
        from ui.app import run
        from ui.site_shell import install_site_shell

        install_site_shell()
    except ModuleNotFoundError as exc:
        if exc.name == "customtkinter":
            message = (
                "CustomTkinter n'est pas installé.\n\n"
                "Sous Windows, double-cliquez simplement sur LANCER.bat : "
                "il installe automatiquement les dépendances nécessaires."
            )
            try:
                import tkinter as tk
                from tkinter import messagebox

                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Asteriax Verse", message)
                root.destroy()
            except Exception:
                print(message, file=sys.stderr)
            return 1
        raise
    try:
        run()
        return 0
    except Exception as exc:
        trace = traceback.format_exc()
        try:
            from core.paths import log_path

            log_path().write_text(trace, encoding="utf-8")
        except Exception:
            pass
        message = (
            "Asteriax Verse a rencontré une erreur inattendue.\n\n"
            f"{exc}\n\nUn rapport a été enregistré dans le dossier local de l'application."
        )
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Asteriax Verse", message)
            root.destroy()
        except Exception:
            print(trace, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
