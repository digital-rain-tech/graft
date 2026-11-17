"""FineReport parameter-panel parsing (ReportParameterAttr).

The parameter panel is a form of nested ``<Widget>``/``<InnerWidget>`` controls:
labels, input editors (date pickers, checkbox combos), and a submit button. Input
editors also become the report's typed `ReportParameter` list.
"""

from __future__ import annotations

from lxml import etree

from graft.models import ParameterWidget, ReportParameter
from graft.readers.finereport_utils import text_of

# InnerWidget class -> normalized widget type.
_WIDGET_TYPES = {
    "Label": "label",
    "DateEditor": "date",
    "ComboCheckBox": "combo_checkbox",
    "ComboBox": "combo_box",
    "TextEditor": "text",
    "NumberEditor": "number",
    "TextArea": "textarea",
    "CheckBox": "checkbox",
    "FormSubmitButton": "button",
    "Button": "button",
}

# Types that are display/action only — excluded from the typed parameter list.
_NON_INPUT_TYPES = {"label", "button"}


def _widget_type(cls: str | None) -> str:
    if not cls:
        return "unknown"
    return _WIDGET_TYPES.get(cls.rsplit(".", 1)[-1], cls.rsplit(".", 1)[-1].lower())


def _label_of(inner: etree._Element, widget_type: str) -> str | None:
    # Labels and buttons carry their caption in widgetValue / Text.
    label_name = inner.find("LabelName")
    if label_name is not None and label_name.get("name"):
        return label_name.get("name")
    if widget_type == "button":
        return text_of(inner.find("Text"))
    value = inner.find("widgetValue")
    if value is not None:
        return text_of(value.find("O"))
    return None


def _default_value(inner: etree._Element) -> str | None:
    value = inner.find("widgetValue")
    if value is None:
        return None
    return text_of(value.find("O"))


def _dictionary_source(inner: etree._Element) -> str | None:
    dictionary = inner.find("Dictionary")
    if dictionary is None:
        return None
    conn = dictionary.find("Connection")
    if conn is None:
        return None
    return text_of(conn.find("DatabaseName"))


def parse_widgets(root: etree._Element) -> list[ParameterWidget]:
    """Parse all parameter-panel controls in document order."""
    attr = root.find("ReportParameterAttr")
    if attr is None:
        return []

    widgets: list[ParameterWidget] = []
    for inner in attr.iter("InnerWidget"):
        name_el = inner.find("WidgetName")
        if name_el is None or not name_el.get("name"):
            continue
        widget_type = _widget_type(inner.get("class"))
        widgets.append(
            ParameterWidget(
                name=name_el.get("name"),
                widget_type=widget_type,
                label=_label_of(inner, widget_type),
                default_value=_default_value(inner) if widget_type != "button" else None,
                data_source=_dictionary_source(inner),
            )
        )
    return widgets


def parse_parameters(widgets: list[ParameterWidget]) -> list[ReportParameter]:
    """Derive typed report parameters from the input (non-label/button) widgets."""
    params: list[ReportParameter] = []
    for w in widgets:
        if w.widget_type in _NON_INPUT_TYPES:
            continue
        params.append(
            ReportParameter(
                name=w.name,
                data_type=w.widget_type,
                default_expression=w.default_value,
                prompt=w.label,
            )
        )
    return params
