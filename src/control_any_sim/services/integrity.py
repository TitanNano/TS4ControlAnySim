from control_any_sim import ui


class IntegrityService:

    is_experimental_reported = False

    @classmethod
    def check_integrety(cls, version):
        if "-" not in version:
            return

        if cls.is_experimental_reported:
            return

        cls.show_experimental_version_dialog(version)
        cls.is_experimental_reported = True

    @staticmethod
    def show_experimental_version_dialog(version):
        dialog = ui.create_dialog(
            title=ui.get_string("0x915E911B"),
            text=ui.get_string("0x098A53E9"),
            dialog_class=ui.UiDialogQuitIgnore
        )

        dialog.show_dialog(additional_tokens=(version,))
