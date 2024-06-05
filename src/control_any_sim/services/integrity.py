"""Service for perforing integrity checks during game startup."""

from __future__ import annotations

from control_any_sim import canys_ui as ui


class IntegrityService:
    """Checks mod integrity during game startup."""

    is_experimental_reported = False

    @classmethod
    def check_integrety(cls: type[IntegrityService], version: str) -> None:
        """Check if the mod is correctly installed."""
        if "-" not in version:
            return

        if cls.is_experimental_reported:
            return

        cls._show_experimental_version_dialog(version)
        cls.is_experimental_reported = True

    @staticmethod
    def _show_experimental_version_dialog(version: str) -> None:
        dialog = ui.create_dialog(
            title=ui.get_string("0x915E911B"),
            text=ui.get_string("0x098A53E9"),
            dialog_class=ui.UiDialogQuitIgnore,
        )

        dialog.show_dialog(additional_tokens=(version,))
