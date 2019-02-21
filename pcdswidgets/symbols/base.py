from pydm.widgets.base import PyDMPrimitiveWidget
from qtpy.QtCore import Property
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                            QSizePolicy, QStyle, QStyleOption)

from ..utils import refresh_style


class ContentLocation(object):
    """
    Enum Class to be used by the widgets to configure the Controls Content
    Location.
    """
    Hidden = 0
    Top = 1
    Bottom = 2
    Left = 3
    Right = 4


class PCDSSymbolBase(QWidget, PyDMPrimitiveWidget):
    """
    Base class to be used for all PCDS Symbols.

    Parameters
    ----------
    parent : QWidget
        The parent widget for this symbol.
    """

    def __init__(self, parent=None, **kwargs):
        super(PCDSSymbolBase, self).__init__(parent=parent, **kwargs)

        self._channels_prefix = None
        self.icon = None

        self._show_icon = True
        self._show_status_tooltip = True
        self._icon_size = -1
        self._controls_location = ContentLocation.Bottom
        self.setup_ui()

    @Property(str)
    def channelsPrefix(self):
        """
        The prefix to be used when composing the channels for each of the
        elements of the symbol widget.

        The prefix must include the protocol as well. E.g.: ca://VALVE

        Returns
        -------
        str
        """
        return self._channels_prefix

    @channelsPrefix.setter
    def channelsPrefix(self, prefix):
        """
        The prefix to be used when composing the channels for each of the
        elements of the symbol widget.

        The prefix must include the protocol as well. E.g.: ca://VALVE

        Parameters
        ----------
        prefix : str
            The prefix to be used for the channels.
        """
        if prefix != self._channels_prefix:
            self._channels_prefix = prefix
            self.destroy_channels()
            self.create_channels()

    @Property(bool)
    def showIcon(self):
        """
        Whether or not to show the symbol icon when rendering the widget.

        Returns
        -------
        bool
        """
        return self._show_icon

    @showIcon.setter
    def showIcon(self, value):
        """
        Whether or not to show the symbol icon when rendering the widget.

        Parameters
        ----------
        value : bool
            Shows the Icon if True, hides it otherwise.
        """
        if value != self._show_icon:
            self._show_icon = value
            if self.icon:
                self.icon.setVisible(self._show_icon)
            self.assemble_layout()

    @Property(bool)
    def showStatusTooltip(self):
        """
        Whether or not to show a detailed status tooltip including the state
        of the widget components such as Interlock, Error, State and more.

        Returns
        -------
        bool
        """
        return self._show_status_tooltip

    @showStatusTooltip.setter
    def showStatusTooltip(self, value):
        """
        Whether or not to show a detailed status tooltip including the state
        of the widget components such as Interlock, Error, State and more.

        Parameters
        ----------
        value : bool
            Displays the tooltip if True.

        """
        if value != self._show_status_tooltip:
            self._show_status_tooltip = value

    @Property(int)
    def iconSize(self):
        """
        The size of the icon in pixels.

        Returns
        -------
        int
        """
        return self._icon_size

    @iconSize.setter
    def iconSize(self, size):
        """
        The size of the icon in pixels.

        Parameters
        ----------
        size : int
            A value > 0 will constrain the size of the icon to the defined
            value.
            If the value is <= 0 it will expand to fill the space available.

        """
        if size <= 0:
            size = - 1
            min_size = 1
            max_size = 999999
            self.icon.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)
            self.icon.setMinimumSize(min_size, min_size)
            self.icon.setMaximumSize(max_size, max_size)

        else:
            self.icon.setFixedSize(size, size)
            self.icon.setSizePolicy(QSizePolicy.Fixed,
                                    QSizePolicy.Fixed)

        self._icon_size = size
        self.icon.update()

    def paintEvent(self, evt):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        This method handles the painting with parameters from the stylesheet.

        Parameters
        ----------
        evt : QPaintEvent
        """
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)
        super(PCDSSymbolBase, self).paintEvent(evt)

    def setup_ui(self):
        """
        Create the inner widgets that are base for all the other symbol
        widgets.
        This method is invoked once at the constructor of the base class.

        Returns
        -------
        None
        """
        self.interlock = QFrame(self)
        self.interlock.setObjectName("interlock")
        self.interlock.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Expanding)

        self.controls_frame = QFrame(self)
        self.controls_frame.setObjectName("controls")
        self.controls_frame.setSizePolicy(QSizePolicy.Maximum,
                                          QSizePolicy.Maximum)
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.interlock)

    def clear(self):
        """
        Remove all inner widgets from the interlock frame layout.
        """
        layout = self.interlock.layout()
        if not layout:
            return
        while layout.count() != 0:
            item = layout.itemAt(0)
            if item is not None:
                layout.removeItem(item)

        # Trick to remove the existing layout by re-parenting it in an
        # empty widget.
        QWidget().setLayout(self.interlock.layout())

    def assemble_layout(self):
        """
        Assembles the widget's inner layout depending on the ContentLocation
        and other configurations set.

        """
        self.clear()

        # (Layout, items)
        widget_map = {
            ContentLocation.Hidden: (QVBoxLayout,
                                     [self.icon]),
            ContentLocation.Top: (QVBoxLayout,
                                  [self.controls_frame,
                                   self.icon]),
            ContentLocation.Bottom: (QVBoxLayout,
                                     [self.icon,
                                      self.controls_frame]),
            ContentLocation.Left: (QHBoxLayout,
                                   [self.controls_frame,
                                    self.icon]),
            ContentLocation.Right: (QHBoxLayout,
                                    [self.icon,
                                     self.controls_frame]),
        }

        layout = widget_map[self._controls_location][0]()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.interlock.setLayout(layout)

        widgets = widget_map[self._controls_location][1]

        controls_visible = self._controls_location != ContentLocation.Hidden
        self.controls_frame.setVisible(controls_visible)

        for widget in widgets:
            if widget == self.controls_frame and not controls_visible:
                continue
            box_layout = QHBoxLayout()
            box_layout.addWidget(widget)
            layout.addLayout(box_layout)

    def status_tooltip(self):
        """
        Assemble and returns the status tooltip for the symbol.

        Returns
        -------
        str
        """
        if hasattr(self, 'NAME'):
            return self.NAME
        else:
            return ""

    def destroy_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        destroyed.
        This method must be implemented on the subclasses and mixins as needed.
        By default this method does nothing.
        """
        pass

    def create_channels(self):
        """
        Method invoked when the channels associated with the widget must be
        created.
        This method must be implemented on the subclasses and mixins as needed.
        By default this method does nothing.
        """
        pass

    def update_stylesheet(self):
        """
        Invoke the stylesheet update process on the widget and child widgets to
        reflect changes on the properties.
        """
        refresh_style(self)

    def update_status_tooltip(self):
        """
        Set the tooltip on the symbol to the content of status_tooltip.
        """
        self.setToolTip(self.status_tooltip())
