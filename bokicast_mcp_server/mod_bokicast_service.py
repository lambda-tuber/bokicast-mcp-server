import sys
from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Slot
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence
import logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QTextEdit
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint

from mod_t_account_widget import TAccountWidget
from mod_journal_entry_widget import JournalEntryWidget

# ロガーの設定
logger = logging.getLogger(__name__)

class BokicastService(QWidget):
    
    def __init__(self):
        super().__init__()
        logger.info(f"BokicastService.__init__: called.")
        self.account_dict: dict[str, TAccountWidget] = {}

        self.main_widget = QWidget()
        self.main_widget.setWindowTitle("Main Container (Floater Test)")
        self.main_widget.setGeometry(0, 0, 100, 100)
        self.main_widget.setStyleSheet("background-color: #F0F0F0;")
        self.main_widget.show()

        self.font = QFont("MS Gothic", 10)
    #
    # セッター
    #
    @Slot(str)
    def journal_entry(self, journal_data):
        j4 = JournalEntryWidget(self.main_widget, "J-004", self.font, self.account_dict)
        journal_data = {
            "debit": [
                {"account": "仕入", "amount": 1000},
                {"account": "荷役費", "amount": 500},
                {"account": "雑費", "amount": 500}
            ],
            "credit": [
                {"account": "買掛金", "amount": 2000}
            ],
            "remarks": "仕訳ID004の例"
        }
        j4.show()
        j4.add_journal(journal_data)
    

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    s = BokicastService()
    s.journal_entry(None)
    sys.exit(app.exec())
