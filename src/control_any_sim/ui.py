from ui.ui_dialog import UiDialogOk, UiDialogResponse, ButtonType  # pylint: disable=import-error,no-name-in-module
from sims4.localization import TunableLocalizedStringFactory  # pylint: disable=import-error


def get_string(string_id):
    return TunableLocalizedStringFactory(default=string_id)


def create_dialog(owner=None, dialog_class=UiDialogOk, **kwargs):
    dialog_factory_loader = dialog_class.TunableFactory(**kwargs)

    dialog_factory = dialog_factory_loader.load_etree_node(None, None, None)
    dialog = dialog_factory(owner)

    return dialog


class UiRequest(UiDialogResponse.UiDialogUiRequest):
    pass


def create_dialog_response(button_type=ButtonType.DIALOG_RESPONSE_CLOSED, text="",
                           ui_request=UiRequest.NO_REQUEST):

    return UiDialogResponse(dialog_response_id=(button_type), text=(text), ui_request=(ui_request))


class UiDialogQuitIgnore(UiDialogOk):
    FACTORY_TUNABLES = {
        'cancel_text': get_string("0x688D35BF"),
        'ok_text': get_string("0x39BA3179")
    }

    @property
    def responses(self):
        return (
            create_dialog_response(
                button_type=ButtonType.DIALOG_RESPONSE_OK,
                text=self.ok_text,
                ui_request=UiRequest.TRANSITION_TO_MAIN_MENU_NO_SAVE
            ),
            create_dialog_response(
                button_type=ButtonType.DIALOG_RESPONSE_CANCEL,
                text=self.cancel_text,
            )
        )
