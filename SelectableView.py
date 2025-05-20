from View import View

class SelectableView(View):
    def __init__(
        self, x: float, y: float,
        width: float, height: float,
        enabled: bool = True
    ) -> None:
        super().__init__(x, y, width, height)
        self.enabled = enabled
        self.selected = False

    def on_select(self) -> None:
        if not self.enabled:
            return
        self.selected = True
        self._mark_dirty()

    def on_deselect(self) -> None:
        if not self.enabled:
            return
        self.selected = False
        self._mark_dirty()