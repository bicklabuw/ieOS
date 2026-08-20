# tests/test_table_view_controller.py
"""Regression tests for TableViewController refresh position preservation."""

import unittest

from gui.ui_kit.TableViewController import TableViewController


class TableViewControllerRefreshTests(unittest.TestCase):
    def test_set_items_preserves_selected_visible_row(self) -> None:
        vc = TableViewController(["Scheduled", "USB", "Schedules at boot: Off"], pop_on_confirm=False)
        vc.select(vc._cells[2])

        vc.set_items(["Scheduled", "USB", "Schedules at boot: On"])

        self.assertIs(vc.selection.current, vc._cells[2])
        self.assertEqual(vc._offset, 0)
        self.assertEqual(vc._cells[2].text, "Schedules at boot: On")

    def test_set_items_preserves_scrolled_offset_and_selection(self) -> None:
        vc = TableViewController(["A", "B", "C", "D", "E", "F"], pop_on_confirm=False)
        vc._offset = 2
        vc._reload_cells()
        vc._update_arrows()
        vc.select(vc._cells[1])

        vc.set_items(["A", "B", "C updated", "D updated", "E updated", "F updated"])

        self.assertEqual(vc._offset, 2)
        self.assertIs(vc.selection.current, vc._cells[1])
        self.assertEqual([cell.text for cell in vc._cells], ["C updated", "D updated", "E updated"])

    def test_set_items_clamps_when_list_shrinks(self) -> None:
        vc = TableViewController(["A", "B", "C", "D", "E", "F"], pop_on_confirm=False)
        vc._offset = 3
        vc._reload_cells()
        vc._update_arrows()
        vc.select(vc._cells[2])

        vc.set_items(["A", "B", "C", "D"])

        self.assertEqual(vc._offset, 1)
        self.assertIs(vc.selection.current, vc._cells[2])
        self.assertEqual([cell.text for cell in vc._cells], ["B", "C", "D"])

    def test_set_items_clears_selection_when_list_becomes_empty(self) -> None:
        vc = TableViewController(["A", "B", "C"], pop_on_confirm=False)
        vc.select(vc._cells[1])

        vc.set_items([])

        self.assertIsNone(vc.selection.current)
        self.assertTrue(all(not cell.visible for cell in vc._cells))
        self.assertTrue(all(not cell.selectable for cell in vc._cells))

    def test_set_sentinel_items_preserves_table_position(self) -> None:
        vc = TableViewController(
            ["A", "B", "C", "D", "E"],
            pop_on_confirm=False,
            sentinel_items=["A"],
        )
        vc._offset = 2
        vc._reload_cells()
        vc._update_arrows()
        vc.select(vc._cells[0])

        vc.set_sentinel_items(["A", "B"])

        self.assertEqual(vc._offset, 2)
        self.assertIs(vc.selection.current, vc._cells[0])
        self.assertEqual([cell.text for cell in vc._cells], ["C", "D", "E"])


if __name__ == "__main__":
    unittest.main()
