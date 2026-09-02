import re


def _sort_key(value):
    text = str(value or "").strip()
    if not text:
        return (0, "")

    if re.fullmatch(r"\d+(?:\.\d+){3}", text):
        try:
            return (1, tuple(int(part) for part in text.split(".")))
        except ValueError:
            pass

    normalized = text.replace(".", "").replace(",", ".")
    try:
        return (2, float(normalized))
    except ValueError:
        return (3, text.casefold())


def make_treeview_sortable(tree):
    """Habilita ordenacao crescente/decrescente ao clicar no cabecalho."""
    sort_state = {}

    def sort_by(column, descending=None):
        if descending is None:
            descending = sort_state.get(column, False)
        sort_state.clear()
        sort_state[column] = not descending

        def value_for(item):
            if column == "#0":
                return tree.item(item, "text")
            return tree.set(item, column)

        items = sorted(
            tree.get_children(""),
            key=lambda item: _sort_key(value_for(item)),
            reverse=descending,
        )
        for index, item in enumerate(items):
            tree.move(item, "", index)

    def attach():
        try:
            tree.heading("#0", command=lambda: sort_by("#0"))
        except Exception:
            pass
        for column in tree["columns"]:
            current = tree.heading(column, "text")
            tree.heading(column, text=current, command=lambda col=column: sort_by(col))

    attach()
    return sort_by
