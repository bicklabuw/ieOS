from gui.ui_core.View import View

class SelectableView(View):
    def __init__(
        self, x: float, y: float,
        width: float, height: float,
        enabled: bool = True
    ) -> None:
        super().__init__(x, y, width, height)
        self.enabled = enabled
        self.selected = False
        self.manager = None

    def add_subview(self, subview: View) -> None:
        super().add_subview(subview)

        if isinstance(subview, SelectableView):
            subview.manager = self.manager
            if self.manager and self == self.manager.current_parent and self.manager.current is None:
                self.manager._enter(0)

    def remove_subview(self, subview: View) -> None:
        if subview in self.subviews:
            if isinstance(subview, SelectableView):
                if subview.selected and self.manager:
                    self.manager.handle_selected_view_being_removed(subview)
            
            self.subviews.remove(subview)
            subview.superview = None
            self._needs_layout = True
            self._mark_dirty()