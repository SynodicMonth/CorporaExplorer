# coding:utf-8
import os
import sys

from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QIcon, QPainter, QImage, QBrush, QColor, QFont, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QFrame, QStackedWidget, QHBoxLayout, QLabel, QListWidgetItem, QVBoxLayout, \
    QWidget, QHeaderView, QFileDialog, QTableWidgetItem, \
    QAbstractItemView, QSizePolicy
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox,
                            isDarkTheme, setTheme, Theme, ListWidget, ToolButton, LineEdit, TreeView,
                            ComboBox, InfoBar, InfoBarPosition, FlowLayout, TableWidget)
from qframelesswindow import FramelessWindow, TitleBar

from content import get_text
from database import CorporaDatabase

database = CorporaDatabase()
FONT = QFont('Segoe UI, Microsoft Yahei UI', 11)


def int_to_size(size):
    size = int(size)
    if size < 1024:
        return str(size) + 'B'
    elif size < 1024 * 1024:
        return str(round(size / 1024, 2)) + 'KB'
    elif size < 1024 * 1024 * 1024:
        return str(round(size / 1024 / 1024, 2)) + 'MB'
    else:
        return str(round(size / 1024 / 1024 / 1024, 2)) + 'GB'


class CustomWidgetItem(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.button = ToolButton(FIF.DELETE, self)
        self.button.setFixedSize(36, 36)
        # align the button to the right
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button, alignment=Qt.AlignRight | Qt.AlignVCenter)

    # set the button's click event
    def click(self, func):
        self.button.clicked.connect(func)


class Widget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.label = QLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        # leave some space for title bar
        self.hBoxLayout.setContentsMargins(0, 32, 0, 0)


class TagsWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.vBoxLayout = QVBoxLayout(self)
        self.listWidget = ListWidget(self)
        self.listWidget.setAlternatingRowColors(True)
        self.refresh()
        self.vBoxLayout.addWidget(self.listWidget)
        self.vBoxLayout.setContentsMargins(0, 42, 24, 24)

        self.add_class_widget = QHBoxLayout(self)

        self.line_edit1 = LineEdit(self)
        self.line_edit1.setFixedHeight(36)
        self.line_edit1.setPlaceholderText('Tag Name')
        self.line_edit1.setContentsMargins(20, 0, 10, 0)

        self.add_class_widget.addWidget(self.line_edit1, alignment=Qt.AlignBottom)

        # add a button to add new class in the bottom right corner
        self.add_button = ToolButton(FIF.ADD, self)
        self.add_button.setFixedSize(36, 36)
        self.add_class_widget.addWidget(self.add_button, alignment=Qt.AlignBottom)
        self.add_button.clicked.connect(self.add_tag)
        self.vBoxLayout.addLayout(self.add_class_widget)
        # self.resize(300, 400)

    def add_tag(self):
        tag_name = self.line_edit1.text()
        if tag_name:
            database.add_tag(tag_name)
            self.line_edit1.clear()
            self.refresh()

    def refresh(self):
        self.listWidget.clear()
        tags = database.get_tags()
        for idx, (tag_id, tag_name) in enumerate(tags):
            widget = CustomWidgetItem(tag_name, self.listWidget)
            widget.click(self.delete_class(tag_id))
            widget.setFixedHeight(48)
            widget.setContentsMargins(0, 0, 10, 0)
            self.listWidget.addItem(tag_name)
            item = self.listWidget.item(idx)
            item.setIcon(FIF.TAG.icon())
            item.setFont(FONT)
            item.setSizeHint(QSize(0, 36))
            self.listWidget.setItemWidget(item, widget)

    def delete_class(self, tag_id):
        def delete():
            database.delete_tag(tag_id)
            self.refresh()

        return delete


class TagWidget(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.label.setFont(FONT)
        # align the text to the center
        self.label.setAlignment(Qt.AlignCenter)
        # its still not centered, so we need to set the text's margin
        self.label.setContentsMargins(2, 2, 2, 6)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(8, 0, 4, 0)
        self.hBoxLayout.addWidget(self.label)
        # add a delete button
        self.button = ToolButton(FIF.CLOSE, self)
        self.button.setFixedSize(24, 24)
        # set the button's background transparent
        self.button.setStyleSheet("background-color: transparent;")
        self.hBoxLayout.addWidget(self.button)
        # add a rounded border

    def paintEvent(self, a0) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#E0E0E0"))
        painter.drawRoundedRect(self.rect(), 8, 8)


class ClassWidget(QFrame):
    def __init__(self, text: str, update_navigation_func: callable, parent=None):
        super().__init__(parent=parent)
        self.update_navigation_func = update_navigation_func
        self.setObjectName(text.replace(' ', '-'))
        self.vBoxLayout = QVBoxLayout(self)
        self.listWidget = ListWidget(self)
        # self.listWidget.setFrameShape(QFrame.NoFrame)

        self.listWidget.setAlternatingRowColors(True)

        self.refresh()

        self.vBoxLayout.addWidget(self.listWidget)
        self.vBoxLayout.setContentsMargins(0, 42, 24, 24)

        self.add_class_widget = QHBoxLayout(self)

        self.line_edit1 = LineEdit(self)
        self.line_edit1.setFixedHeight(36)
        self.line_edit1.setPlaceholderText('Class Name')
        self.line_edit1.setContentsMargins(20, 0, 10, 0)

        self.line_edit2 = LineEdit(self)
        self.line_edit2.setFixedHeight(36)
        self.line_edit2.setPlaceholderText('Teacher Name')
        self.line_edit2.setContentsMargins(0, 0, 10, 0)
        self.add_class_widget.addWidget(self.line_edit1, alignment=Qt.AlignBottom)
        self.add_class_widget.addWidget(self.line_edit2, alignment=Qt.AlignBottom)

        # add a button to add new class in the bottom right corner
        self.add_button = ToolButton(FIF.ADD, self)
        self.add_button.setFixedSize(36, 36)
        self.add_class_widget.addWidget(self.add_button, alignment=Qt.AlignBottom)
        self.add_button.clicked.connect(self.add_class)
        self.vBoxLayout.addLayout(self.add_class_widget)
        # self.resize(300, 400)

    def add_class(self):
        class_name = self.line_edit1.text()
        teacher_name = self.line_edit2.text()
        print("add", class_name, teacher_name)
        try:
            database.add_class(class_name, teacher_name)
        except RuntimeError:
            InfoBar.error(
                title='ERROR',
                content="课程名不能为空",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            return
        self.line_edit1.clear()
        self.line_edit2.clear()
        self.refresh()

    def refresh(self):
        self.update_navigation_func()
        self.listWidget.clear()
        classes = database.get_classes()
        for idx, (class_id, class_name, teacher_name) in enumerate(classes):
            name = class_name + "    by: " + teacher_name
            widget = CustomWidgetItem(name, self.listWidget)
            widget.click(self.delete_class(class_id))
            widget.setFixedHeight(36)
            widget.setContentsMargins(0, 0, 10, 0)
            self.listWidget.addItem(name)
            item = self.listWidget.item(idx)
            item.setIcon(FIF.BOOK_SHELF.icon())
            item.setFont(FONT)
            item.setSizeHint(QSize(0, 36))
            self.listWidget.setItemWidget(item, widget)

    def delete_class(self, class_id):
        def delete():
            database.delete_class(class_id)
            self.refresh()

        return delete


class FilelistWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.class_id = None
        self.filelist = {}
        self.chapter_names = {}
        self.current_file_id = None
        self.tags = []

        # main layout
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(24, 40, 16, 16)

        # set up the tree view
        self.view = TreeView(self)
        self.model = QStandardItemModel()
        self.rootNode = self.model.invisibleRootItem()
        self.view.setModel(self.model)
        self.header = self.view.header()
        self.header.setStyleSheet("QHeaderView::section {background-color: transparent;}")
        self.header.setFont(FONT)
        self.header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.header.setFixedHeight(32)
        self.model.setHorizontalHeaderLabels(['          File Name', '    Type', '     Size', ' '])
        # align the header text to the left
        self.header.setSectionResizeMode(0, QHeaderView.Interactive)
        self.header.resizeSection(0, 500)
        self.header.resizeSection(1, 100)
        self.header.resizeSection(2, 100)
        self.header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.header.resizeSection(3, 100)
        self.header.setStretchLastSection(False)
        # self.header.setOffset(-50)
        self.view.setUniformRowHeights(True)
        self.view.doubleClicked.connect(self.doubleclick_handler)
        self.view.clicked.connect(self.click_handler)
        self.view.setAlternatingRowColors(True)
        self.vBoxLayout.addWidget(self.view)

        # tags ui
        self.tags_area = FlowLayout(self.vBoxLayout.widget())
        self.tags_area.setContentsMargins(20, 0, 0, 0)
        self.vBoxLayout.addLayout(self.tags_area)

        # add tag ui
        self.add_tag_widget = QHBoxLayout(self)
        self.text_add_tag = QLabel("Add a tag: ", self)
        self.text_add_tag.setFont(FONT)
        self.text_add_tag.setFixedHeight(36)
        self.text_add_tag.setContentsMargins(20, 0, 10, 0)
        self.add_tag_widget.addWidget(self.text_add_tag, alignment=Qt.AlignBottom | Qt.AlignLeft)
        self.tag_combo_box = ComboBox(self)
        self.tag_combo_box.setFixedHeight(36)
        # strech the combo box to the right
        self.tag_combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_tag_widget.addWidget(self.tag_combo_box, alignment=Qt.AlignBottom)
        self.add_button2 = ToolButton(FIF.ADD, self)
        self.add_button2.setFixedSize(36, 36)
        self.add_button2.clicked.connect(self.add_tag)
        self.add_tag_widget.addWidget(self.add_button2, alignment=Qt.AlignBottom | Qt.AlignRight)
        self.vBoxLayout.addLayout(self.add_tag_widget)

        # add chapter ui
        self.add_chapter_widget = QHBoxLayout(self)
        # self.add_chapter_widget.setContentsMargins(24, 0, 0, 0)
        self.text_chapter = QLabel("Add a chapter: ", self)
        self.text_chapter.setFont(FONT)
        self.text_chapter.setFixedHeight(36)
        self.text_chapter.setContentsMargins(20, 0, 10, 0)
        self.add_chapter_widget.addWidget(self.text_chapter, alignment=Qt.AlignBottom | Qt.AlignLeft)
        self.line_edit = LineEdit(self)
        self.line_edit.setFixedHeight(36)
        self.line_edit.setPlaceholderText('Chapter name')
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_chapter_widget.addWidget(self.line_edit, alignment=Qt.AlignBottom)
        self.add_button1 = ToolButton(FIF.ADD, self)
        self.add_button1.setFixedSize(36, 36)
        self.add_button1.clicked.connect(self.add_chapter)
        self.add_chapter_widget.addWidget(self.add_button1, alignment=Qt.AlignBottom | Qt.AlignRight)
        self.vBoxLayout.addLayout(self.add_chapter_widget)

        # add file ui
        self.add_file_widget = QHBoxLayout(self)
        # self.add_file_widget.setContentsMargins(24, 0, 0, 0)
        self.text_file = QLabel("Add a file: ", self)
        self.text_file.setFont(FONT)
        self.text_file.setFixedHeight(36)
        self.text_file.setContentsMargins(20, 0, 10, 0)
        self.add_file_widget.addWidget(self.text_file, alignment=Qt.AlignBottom | Qt.AlignLeft)
        self.combo_box = ComboBox(self)
        self.combo_box.setFixedHeight(36)
        self.combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_file_widget.addWidget(self.combo_box, alignment=Qt.AlignBottom)
        self.add_button = ToolButton(FIF.ADD, self)
        self.add_button.setFixedSize(36, 36)
        self.add_button.clicked.connect(self.add_file)
        self.add_file_widget.addWidget(self.add_button, alignment=Qt.AlignBottom | Qt.AlignRight)
        self.vBoxLayout.addLayout(self.add_file_widget)

        # initialize
        self.refresh()
        self.refresh_tags()

    def refresh(self):
        print('refresh')
        if self.class_id:
            self.filelist, self.chapter_names = database.get_files(self.class_id)
            font = FONT
            font.setPointSize(12)
            print(self.filelist)
            # filelist = {1: (('file1', 'type1', 'size1'), ('file2', 'type2', 'size2')),
            #             2: (('file3', 'type3', 'size3'))}
            self.rootNode.removeRows(0, self.rootNode.rowCount())
            for chapter, files in self.filelist.items():
                section_node = QStandardItem(self.chapter_names[chapter][0])
                section_node.setIcon(FIF.FOLDER.icon())
                section_node.setEditable(False)
                section_node2 = QStandardItem('')
                section_node2.setEditable(False)
                section_node3 = QStandardItem(int_to_size(self.chapter_names[chapter][1]
                                                          if self.chapter_names[chapter][1] else 0))
                section_node3.setEditable(False)
                section_node4 = QStandardItem('')
                section_node4.setEditable(False)
                del_button = ToolButton(FIF.CLOSE, self)
                # make button transparent
                del_button.setStyleSheet("background-color: transparent;")
                del_button.setFixedSize(20, 20)
                del_button.clicked.connect(self.delete_chapter(chapter))
                # set text size
                section_node.setFont(font)
                section_node2.setFont(font)
                section_node3.setFont(font)
                self.rootNode.appendRow([section_node, section_node2, section_node3, section_node4])
                self.view.setIndexWidget(section_node4.index(), del_button)
                for file in files:
                    file_node = QStandardItem(file[1])
                    file_node.setIcon(FIF.DOCUMENT.icon())
                    file_node.setEditable(False)
                    type_node = QStandardItem(file[3])
                    type_node.setEditable(False)
                    size_node = QStandardItem(int_to_size(file[4] if file[4] else 0))
                    size_node.setEditable(False)
                    del_node = QStandardItem('')
                    del_node.setEditable(False)
                    # set text size
                    file_node.setFont(font)
                    type_node.setFont(font)
                    size_node.setFont(font)
                    del_button = ToolButton(FIF.CLOSE, self)
                    # make button transparent
                    del_button.setStyleSheet("background-color: transparent;")
                    del_button.setFixedSize(20, 20)
                    del_button.clicked.connect(self.delete_file(file[0]))
                    section_node.appendRow([file_node, type_node, size_node, del_node])
                    self.view.setIndexWidget(del_node.index(), del_button)

        self.view.expandAll()
        self.combo_box.clear()
        self.combo_box.addItems([x[0] for x in self.chapter_names.values()])
        self.tag_combo_box.clear()
        self.tags = list(database.get_tags())
        print("tags:", self.tags)
        self.tag_combo_box.addItems([x[1] for x in self.tags])

    def change_class(self, class_id):
        self.class_id = class_id
        self.refresh()

    def add_chapter(self):
        if self.class_id and self.line_edit.text():
            database.add_chapter(self.class_id, self.line_edit.text())
            self.refresh()

    def add_file(self):
        if self.class_id:
            if self.combo_box.currentIndex() == -1:
                InfoBar.error(
                    title='ERROR',
                    content="请选择一个章节或新建一个章节",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
                return
            chapter_id = list(self.chapter_names.keys())[self.combo_box.currentIndex()]
            files = QFileDialog.getOpenFileNames(self, "选择文件", "D://Document")[0]
            print(files)
            for file in files:
                if file:
                    file_name = file.split('/')[-1]
                    file_type = file.split('.')[-1]
                    file_size = str(os.path.getsize(file))
                    file_id = database.add_file(file_name, file, file_type, file_size, chapter_id, self.class_id)
                    try:
                        content = get_text(file, file_type)
                        database.add_textfile(file_id, content)
                    except Exception as e:
                        print("error:", e)
                        pass
            self.refresh()

    def delete_chapter(self, chapter_id):
        def delete():
            database.delete_chapter(chapter_id)
            self.refresh()

        return delete

    def delete_file(self, file_id):
        def delete():
            database.delete_file(file_id)
            self.refresh()

        return delete

    def doubleclick_handler(self, index):
        # if item is a file, open it
        if index.parent().row() != -1:
            file_id, file_name, file_path, file_type, file_size = \
                self.filelist[list(self.chapter_names.keys())[index.parent().row()]][index.row()]
            if file_type in ['txt', 'py', 'c', 'cpp', 'java', 'html', 'css', 'js', 'php', 'sql', 'xml', 'json']:
                # open file using default editor
                print("open", file_path)
                os.system(f'notepad {file_path}')
            elif file_type in ['jpg', 'png', 'bmp', 'gif', 'jpeg', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
                os.system(f'start {file_path}')
            else:
                InfoBar.error(
                    title='ERROR',
                    content="未知的文件类型",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )

    def click_handler(self, index):
        if index.parent().row() == -1:
            # self.chapter_id = list(self.chapter_names.keys())[index.row()]
            self.combo_box.setCurrentIndex(index.row())
        else:
            file_id, file_name, file_path, file_type, file_size = \
                self.filelist[list(self.chapter_names.keys())[index.parent().row()]][index.row()]
            self.current_file_id = file_id
            self.refresh_tags()

    def refresh_tags(self):
        print("refresh tags")
        self.tags_area.takeAllWidgets()
        if not self.current_file_id:
            return
        print("current file id:", self.current_file_id)
        tag_names = database.get_filetags(self.current_file_id)
        for tag_id, tag_name in tag_names:
            tag = TagWidget(tag_name, self)
            tag.setFont(FONT)
            tag.button.clicked.connect(self.delete_tag(self.current_file_id, tag_id))
            self.tags_area.addWidget(tag)
        self.tags_area.update()

    def add_tag(self):
        if not self.current_file_id:
            return
        tag_id = list(self.tags)[self.tag_combo_box.currentIndex()][0]
        database.add_filetag(self.current_file_id, tag_id)
        print("add tag", tag_id)
        self.refresh_tags()

    def delete_tag(self, file_id, tag_id):
        def delete():
            database.delete_filetag(file_id, tag_id)
            self.refresh_tags()

        return delete


class FilesWidget(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent=parent)
        self.files = []
        self.setObjectName(text.replace(' ', '-'))
        self.vBoxLayout = QVBoxLayout(self)
        self.tableView = TableWidget(self)
        self.tableView.setWordWrap(False)
        self.tableView.setRowHeight(0, 36)
        self.tableView.setColumnCount(3)
        # make it resizable, but default size is fixed
        self.tableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tableView.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableView.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.horizontalHeader().setMinimumSectionSize(100)
        self.tableView.horizontalHeader().setMaximumSectionSize(500)
        # set to 300 by default
        self.tableView.setColumnWidth(0, 500)
        self.tableView.setColumnWidth(1, 150)
        self.tableView.setColumnWidth(2, 150)
        self.tableView.horizontalHeader().setStyleSheet("background-color: transparent;")
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.horizontalHeader().setFixedHeight(32)
        self.tableView.setShowGrid(False)
        # not editable
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.vBoxLayout.addWidget(self.tableView)
        self.vBoxLayout.setContentsMargins(24, 42, 24, 24)
        self.vBoxLayout.setSpacing(0)
        self.refresh()

    def refresh(self):
        self.tableView.clear()
        self.tableView.setHorizontalHeaderLabels(['File', 'Class', 'Chapter'])
        # self.tableView.horizontalHeader().setFont(FONT)
        self.files = database.get_all_files()
        print(self.files)
        self.tableView.setRowCount(len(self.files) + 1)
        for idx, (class_name, chapter_name, file_name) in enumerate(self.files):
            file_item = QTableWidgetItem(file_name)
            file_item.setIcon(FIF.DOCUMENT.icon())
            file_item.setFont(FONT)
            class_item = QTableWidgetItem(class_name)
            class_item.setFont(FONT)
            chapter_item = QTableWidgetItem(chapter_name)
            chapter_item.setFont(FONT)
            self.tableView.setItem(idx, 0, file_item)
            self.tableView.setItem(idx, 1, class_item)
            self.tableView.setItem(idx, 2, chapter_item)
        self.tableView.update()


class SearchWidget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.result_list = []
        self.setObjectName(text.replace(' ', '-'))
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(24, 42, 24, 24)

        self.hBoxLayout = QHBoxLayout(self)
        # add a search bar
        self.search_bar = LineEdit(self)
        self.search_bar.setPlaceholderText("搜索")
        self.search_bar.setFixedHeight(36)
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.returnPressed.connect(self.search)
        self.hBoxLayout.addWidget(self.search_bar, alignment=Qt.AlignTop)
        # add a search button
        self.search_button = ToolButton(FIF.SEARCH, self)
        self.search_button.setFixedSize(36, 36)
        self.search_button.clicked.connect(self.search)
        self.hBoxLayout.addWidget(self.search_button, alignment=Qt.AlignTop)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.vBoxLayout.addLayout(self.hBoxLayout)

        self.listWidget = ListWidget(self)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.doubleClicked.connect(self.doubleclick_handler)
        self.vBoxLayout.addWidget(self.listWidget)

    def search(self):
        text = self.search_bar.text()
        result = database.search(text)
        self.listWidget.clear()
        self.result_list = []
        for file_id, content in result:
            item = QListWidgetItem()
            file_name, file_address, file_type, file_size = database.get_file_info(file_id)
            item.setIcon(FIF.DOCUMENT.icon())
            item.setText(file_name)
            item.setToolTip(file_address)
            item.setSizeHint(QSize(0, 36))
            item.setFont(FONT)
            item1 = QListWidgetItem()
            item1.setText(self.format_search_result(content, text))
            item1.setToolTip(file_address)
            item1.setSizeHint(QSize(0, 36))
            font = QFont()
            font.setFamily("Segoe UI, Microsoft YaHei UI")
            font.setStyle(QFont.StyleItalic)
            font.setPointSize(11)
            item1.setFont(font)
            item1.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # print(self.format_search_result(content, text))
            self.listWidget.addItem(item)
            self.listWidget.addItem(item1)
            self.result_list.append((file_id, file_name, file_address, file_type, file_size))

    def format_search_result(self, content, keyword):
        """get the content near the keyword
        add ... before and after the content
        match the keyword with red color
        """
        content = content.replace('\n', ' ')
        index = content.find(keyword)
        if index == -1:
            return content
        else:
            if index < 0:
                start = 0
            else:
                start = index - 0
            if index + 100 > len(content):
                end = len(content)
            else:
                end = index + 100
            content = content[start:end]
            if start != 0:
                content = '...' + content
            if end != len(content):
                content = content + '...'
            return content

    def doubleclick_handler(self, index):
        file_id, file_name, file_path, file_type, file_size = self.result_list[index.row() // 2]
        if file_type in ['txt', 'py', 'c', 'cpp', 'java', 'html', 'css', 'js', 'php', 'sql', 'xml', 'json']:
            # open file using default editor
            print("open", file_path)
            os.system(f'notepad {file_path}')
        elif file_type in ['jpg', 'png', 'bmp', 'gif', 'jpeg', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
            os.system(f'start {file_path}')
        else:
            InfoBar.error(
                title='ERROR',
                content="未知的文件类型",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )


class AvatarWidget(NavigationWidget):
    """ Avatar widget """

    def __init__(self, parent=None):
        super().__init__(isSelectable=False, parent=parent)
        self.avatar = QImage('../resource/profile.jpg').scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # draw background
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # draw avatar
        painter.setBrush(QBrush(self.avatar))
        painter.translate(8, 6)
        painter.drawEllipse(0, 0, 24, 24)
        painter.translate(-8, -6)

        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            font = FONT
            font.setPixelSize(14)
            painter.setFont(font)
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, 'Synodic')


class CustomTitleBar(TitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)
        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertSpacing(0, 10)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))


class Window(FramelessWindow):

    def __init__(self):
        super().__init__()
        # datas
        self.classes = []
        self.class_bars = []

        self.setTitleBar(CustomTitleBar(self))

        # use dark theme mode
        setTheme(Theme.LIGHT)

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(self, showMenuButton=True, showReturnButton=False)
        self.stackWidget = QStackedWidget(self)

        # create sub interface
        self.searchInterface = SearchWidget('Search', self)
        self.classesInterface = ClassWidget('My Classes', self.update_navigation_bar, self)
        self.tagsInterface = TagsWidget('Tags', self)
        self.filesInterface = FilesWidget('Files', self)
        self.filelistInterface = FilelistWidget(self)
        self.stackWidget.addWidget(self.filelistInterface)

        # initialize layout
        self.init_layout()

        # add items to navigation interface
        self.init_navigation()

        self.init_window()

    def init_layout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)

    def init_navigation(self):
        self.add_sub_interface(self.searchInterface, FIF.SEARCH, 'Search')
        self.add_sub_interface(self.classesInterface, FIF.BOOK_SHELF, 'My Classes')
        self.add_sub_interface(self.tagsInterface, FIF.TAG, 'Tags')
        self.addFilesInterface(self.filesInterface, FIF.DOCUMENT, 'Files')
        # self.addSubInterface(self.filelistInterface, FIF.SETTING, 'Setting')

        self.navigationInterface.addSeparator()

        self.update_navigation_bar()

        # add custom widget to bottom
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=AvatarWidget(),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM
        )

        # self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

        # !IMPORTANT: don't forget to set the default route key
        self.navigationInterface.setDefaultRouteKey(self.classesInterface.objectName())

        # set the maximum width
        # self.navigationInterface.setExpandWidth(300)

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(1)

    def init_window(self):
        self.resize(1100, 700)
        self.setWindowIcon(QIcon('../resource/icon.png'))
        self.setWindowTitle('CorporaExplorer')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)
        self.navigationInterface.setExpandWidth(250)
        self.navigationInterface.panel.expand()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.setQss()

    def add_sub_interface(self, interface, icon, text: str, position=NavigationItemPosition.TOP):
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text
        )

    def addFilesInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP):
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=self.update_files,
            position=position,
            tooltip=text
        )

    def setQss(self):
        color = 'dark' if isDarkTheme() else 'light'
        with open(f'../resource/{color}/demo.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())

    def showMessageBox(self):
        w = MessageBox(
            'CorporaExplorer',
            'CorporaExplorer is a tool for exploring your classfiles easily.\n'
            'by Synodic, Nankai University.\n',
            self
        )
        w.exec()

    def resizeEvent(self, e):
        self.titleBar.move(46, 0)
        self.titleBar.resize(self.width() - 46, self.titleBar.height())

    def update_navigation_bar(self):
        for i in range(len(self.classes)):
            self.navigationInterface.removeWidget(str(self.classes[i][0]))
        self.class_bars = []
        self.classes = database.get_classes()
        for cls in self.classes:
            cls_button = self.navigationInterface.addItem(
                str(cls[0]),
                FIF.FOLDER,
                cls[1],
                self.update_filelist(cls[0]),
                position=NavigationItemPosition.SCROLL
            )
            self.class_bars.append(cls_button)

    def update_filelist(self, class_id):
        def func():
            self.filelistInterface.change_class(class_id)
            self.switchTo(self.filelistInterface)

        return func

    def update_files(self):
        self.filesInterface.refresh()
        self.switchTo(self.filesInterface)


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()
