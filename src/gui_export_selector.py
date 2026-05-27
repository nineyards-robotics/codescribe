# -*- coding: utf-8 -*-
# REMEMBER: this is python 2.7
import clr
from System.Windows.Forms import (Application, Form, TreeView, TreeNode, 
                                   Button, Panel, DockStyle, AnchorStyles)
from System.Drawing import Size, Point

from object_type import ObjectType, get_object_type

# Типы, которые НЕ должны отображаться в дереве (нельзя выбрать отдельно)
EXCLUDED_TYPES = {
    ObjectType.METHOD,
    ObjectType.PROPERTY,
    ObjectType.ACTION,
    ObjectType.TRANSITION,
    ObjectType.INTERFACE_METHOD,
    ObjectType.GET_ACCESSOR,
    ObjectType.INTERFACE_GET_ACCESSOR,
    ObjectType.ABSTRACT_CLASS_METHOD,
    ObjectType.CALL_TO_POU,
}

def is_selectable(obj_type):
    """Можно ли выбирать объект данного типа."""
    return obj_type not in EXCLUDED_TYPES

def build_tree_nodes(parent_node, parent_obj):
    """Рекурсивно строит узлы дерева."""
    for child in parent_obj.get_children():
        child_type = get_object_type(child)
        if not is_selectable(child_type):
            # Всё равно обходим детей, т.к. среди них могут быть выбираемые
            build_tree_nodes(parent_node, child)
            continue
        
        node = TreeNode(child.get_name())
        node.Tag = child  # сохраняем ссылку на объект CODESYS
        parent_node.Nodes.Add(node)
        build_tree_nodes(node, child)

class ExportSelectorForm(Form):
    def __init__(self, root_objects):
        self.SelectedObjects = []
        self.Text = "Выбор объектов для экспорта"
        self.Size = Size(400, 500)
        self.StartPosition = 1  # CenterScreen
        
        # Панель для дерева
        self.tree = TreeView()
        self.tree.Dock = DockStyle.Fill
        self.tree.CheckBoxes = True
        self.tree.AfterCheck += self.on_after_check
        
        # Заполняем дерево
        for root_obj in root_objects:
            root_node = TreeNode(root_obj.get_name())
            root_node.Tag = root_obj
            self.tree.Nodes.Add(root_node)
            build_tree_nodes(root_node, root_obj)
        
        # Кнопки
        btn_panel = Panel()
        btn_panel.Height = 40
        btn_panel.Dock = DockStyle.Bottom
        
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.Location = Point(btn_panel.Width - 90, 5)
        btn_ok.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        btn_ok.Click += self.on_ok
        
        btn_cancel = Button()
        btn_cancel.Text = "Отмена"
        btn_cancel.Location = Point(btn_panel.Width - 180, 5)
        btn_cancel.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        btn_cancel.Click += self.on_cancel
        
        btn_panel.Controls.Add(btn_ok)
        btn_panel.Controls.Add(btn_cancel)
        
        self.Controls.Add(self.tree)
        self.Controls.Add(btn_panel)
    
    def on_after_check(self, sender, args):
        # При чеке/анчеке узла – синхронизируем детей (опционально)
        # Если нужно, чтобы при снятии чека с родителя снимались все дети – раскомментировать
        # node = args.Node
        # if not node.Checked:
        #     for child in node.Nodes:
        #         child.Checked = False
        pass
    
    def collect_checked(self, node):
        """Рекурсивно собирает все отмеченные объекты."""
        if node.Checked and node.Tag is not None:
            self.SelectedObjects.append(node.Tag)
        for child in node.Nodes:
            self.collect_checked(child)
    
    def on_ok(self, sender, args):
        self.collect_checked(self.tree.Nodes[0])  # начинаем с корня
        self.DialogResult = 1  # OK
        self.Close()
    
    def on_cancel(self, sender, args):
        self.DialogResult = 2  # Cancel
        self.Close()

def select_objects(root_objects):
    """
    Показывает диалог выбора объектов.
    root_objects – список объектов (например, список устройств или Application)
    Возвращает список выбранных объектов CODESYS.
    """
    form = ExportSelectorForm(root_objects)
    result = form.ShowDialog()
    if result == 1:
        return form.SelectedObjects
    else:
        return []