from graft.readers.finereport_utils import parse_cpt
from graft.readers.finereport_widgets import parse_parameters, parse_widgets

SAMPLE = "tests/fixtures/finereport/checkbox_multi_condition_query.cpt"


def _widgets():
    return parse_widgets(parse_cpt(SAMPLE))


def _by_name(widgets, name):
    return next(w for w in widgets if w.name == name)


def test_all_panel_widgets_parsed():
    names = [w.name for w in _widgets()]
    assert names == [
        "label1",
        "Opening",
        "label3",
        "Ending",
        "label5",
        "Select_warehouse",
        "formSubmit0",
    ]


def test_date_editor_widget():
    w = _by_name(_widgets(), "Opening")
    assert w.widget_type == "date"
    assert w.label == "Opening:"
    assert w.default_value == "1264953600000"


def test_combo_checkbox_widget_backed_by_dictionary():
    w = _by_name(_widgets(), "Select_warehouse")
    assert w.widget_type == "combo_checkbox"
    assert w.label == "Select warehouse:"
    assert w.default_value == "Warehouse 1,Warehouse 3"
    assert w.data_source == "FRDemo"


def test_label_and_button_widgets():
    label = _by_name(_widgets(), "label1")
    assert label.widget_type == "label"
    assert label.label == "Opening:"
    button = _by_name(_widgets(), "formSubmit0")
    assert button.widget_type == "button"
    assert button.label == "Generate inventory accounting"


def test_parameters_are_input_widgets_only():
    params = parse_parameters(_widgets())
    assert [p.name for p in params] == ["Opening", "Ending", "Select_warehouse"]
    opening = params[0]
    assert opening.data_type == "date"
    assert opening.prompt == "Opening:"
