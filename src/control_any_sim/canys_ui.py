"""Collection of UI components for this mod."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from sims4.localization import (
    TunableLocalizedStringFactory,
)
from ui.ui_dialog import (
    ButtonType,
    UiDialog,
    UiDialogOk,
    UiDialogResponse,
)

if TYPE_CHECKING:
    from typing_extensions import Self


def get_string(string_id: str) -> str:
    """Get a localized string from the string tables."""
    return TunableLocalizedStringFactory(default=string_id)


def create_dialog(
    owner: None = None,
    dialog_class: type[UiDialog] = UiDialogOk,
    **kwargs: str,
) -> UiDialog:
    """Create a new dialog for a given dialog class."""
    dialog_factory_loader = dialog_class.TunableFactory(**kwargs)

    dialog_factory = dialog_factory_loader.load_etree_node(None, None, None)
    return dialog_factory(owner)


class UiRequest(UiDialogResponse.UiDialogUiRequest):
    """Helper class to simplify the dialog request."""


def create_dialog_response(
    button_type: ButtonType = ButtonType.DIALOG_RESPONSE_CLOSED,
    text: str = "",
    ui_request: UiRequest = UiRequest.NO_REQUEST,
) -> UiDialogResponse:
    """Create a new dialog response option."""
    return UiDialogResponse(
        dialog_response_id=(button_type),
        text=(text),
        ui_request=(ui_request),
    )


class UiDialogQuitIgnore(UiDialogOk):
    """A UI dialog that asks the user if they want to quit or ignore the message."""

    FACTORY_TUNABLES: MappingProxyType[str, str] = MappingProxyType(
        {
            "cancel_text": get_string("0x688D35BF"),
            "ok_text": get_string("0x39BA3179"),
        },
    )

    @property
    def responses(self: Self) -> tuple[UiDialogResponse, UiDialogResponse]:
        """Response options of this dialog."""
        return (
            create_dialog_response(
                button_type=ButtonType.DIALOG_RESPONSE_OK,
                text=self.ok_text,
                ui_request=UiRequest.TRANSITION_TO_MAIN_MENU_NO_SAVE,
            ),
            create_dialog_response(
                button_type=ButtonType.DIALOG_RESPONSE_CANCEL,
                text=self.cancel_text,
            ),
        )
