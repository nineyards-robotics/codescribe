
    # -*- coding: utf-8 -*-
# REMEMBER: this is python 2.7

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import (
    Form, TreeView, TreeNode, Button, Panel, DockStyle,
    FormStartPosition, FormBorderStyle, DialogResult
)
from System.Drawing import Size, Point

from object_type import get_object_type, ObjectType

# if you need to hide some types, add them here
EXCLUDED_TYPES = set([
])

def is_selectable(obj_type):
    return obj_type not in EXCLUDED_TYPES

def build_tree_nodes(parent_node, parent_obj):
    parent_type = get_object_type(parent_obj)

    for child in parent_obj.get_children():
        child_type = get_object_type(child)

        if child_type == ObjectType.FOLDER:
            node = TreeNode(child.get_name())
            node.Tag = child
            parent_node.Nodes.Add(node)
            build_tree_nodes(node, child)
            continue

        if parent_type == ObjectType.FOLDER and is_selectable(child_type):
            node = TreeNode(child.get_name())
            node.Tag = child
            parent_node.Nodes.Add(node)

class ExportSelectorForm(Form):
    def __init__(self, root_objects):
        Form.__init__(self)

        self.SelectedObjects = []
        self._syncing_checks = False

        self.Text = "Select Objects for Export"
        self.Size = Size(600, 700)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MinimizeBox = False

        self.btn_panel = Panel()
        self.btn_panel.Dock = DockStyle.Bottom
        self.btn_panel.Height = 50

        self.btn_ok = Button()
        self.btn_ok.Text = "OK"
        self.btn_ok.Size = Size(90, 28)
        self.btn_ok.Location = Point(390, 10)
        self.btn_ok.Click += self.on_ok

        self.btn_cancel = Button()
        self.btn_cancel.Text = "Cancel"
        self.btn_cancel.Size = Size(90, 28)
        self.btn_cancel.Location = Point(490, 10)
        self.btn_cancel.Click += self.on_cancel

        self.btn_panel.Controls.Add(self.btn_ok)
        self.btn_panel.Controls.Add(self.btn_cancel)

        self.tree = TreeView()
        self.tree.Dock = DockStyle.Fill
        self.tree.CheckBoxes = True
        self.tree.AfterCheck += self.on_after_check

        for root_obj in root_objects:
            root_node = TreeNode(root_obj.get_name())
            root_node.Tag = root_obj
            self.tree.Nodes.Add(root_node)
            build_tree_nodes(root_node, root_obj)
            root_node.Expand()

        self.Controls.Add(self.btn_panel)
        self.Controls.Add(self.tree)

    def set_checked_recursive(self, node, checked):
        for child in node.Nodes:
            child.Checked = checked
            self.set_checked_recursive(child, checked)

    def on_after_check(self, sender, args):
        if self._syncing_checks:
            return

        self._syncing_checks = True
        try:
            self.set_checked_recursive(args.Node, args.Node.Checked)
        finally:
            self._syncing_checks = False

    def collect_top_checked(self, node):
        if node.Checked and node.Tag is not None:
            self.SelectedObjects.append(node.Tag)
            return

        for child in node.Nodes:
            self.collect_top_checked(child)

    def on_ok(self, sender, args):
        self.SelectedObjects = []
        for i in range(self.tree.Nodes.Count):
            self.collect_top_checked(self.tree.Nodes[i])
        self.DialogResult = DialogResult.OK
        self.Close()

    def on_cancel(self, sender, args):
        self.DialogResult = DialogResult.Cancel
        self.Close()

def select_objects(root_objects):
    form = ExportSelectorForm(root_objects)
    result = form.ShowDialog()
    if result == DialogResult.OK:
        return form.SelectedObjects
    return []

  