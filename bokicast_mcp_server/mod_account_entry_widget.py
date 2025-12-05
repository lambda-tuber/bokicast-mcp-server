from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractScrollArea
)
from PySide6.QtGui import QFont, QFontMetrics, QMouseEvent
from PySide6.QtCore import Qt, QPoint
import sys
from typing import Optional, Tuple

import logging
logger = logging.getLogger(__name__)

class AccountEntryWidget(QWidget):
    _drag_start_position: QPoint | None = None  # 💡 ドラッグ開始位置を保持するメンバー変数
    _single_row_height: int = 0
    _table_header_height: int = 0
    
    # 💡 スナップ距離を定義（このピクセル数以内に近づくと引っ付く）
    SNAP_DISTANCE = 15 

    def __init__(self, parent, title, font, hcolor, enable_drag=True):
        super().__init__(parent)
        
        self.enable_drag = enable_drag # フラグを保持
        if self.enable_drag:
            # 💡 ドラッグ有効時: フローティングウィンドウとして設定
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, False) 
            self.setCursor(Qt.OpenHandCursor) 
        else:
            # 💡 ドラッグ無効時: 通常の埋め込みウィジェットとして設定
            self.setWindowFlags(Qt.Widget)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WA_StyledBackground, True)
            self.setCursor(Qt.ArrowCursor)
            
        self.header_color = hcolor
        self.setContentsMargins(4, 4, 4, 4)
        self.setObjectName("AccountFrame")

        # ---- フォント設定（パラメータ化） ----
        self.font = font
        self.fm = QFontMetrics(self.font)

        # ---- レイアウト ----
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # ---- 上部ヘッダー（タイトルラベル） ----
        self.header_label = QLabel(title)
        self.header_label.setFont(self.font)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet(f"background-color: {self.header_color}; border: 0px solid black;")
        self.layout.addWidget(self.header_label, alignment=Qt.AlignTop)

        # ---- テーブル（2列：勘定科目 / 金額） ----
        self.table = QTableWidget(0, 2)
        self.table.setFont(self.font)
        self.table.setStyleSheet("border: 0px solid black;")
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.layout.addWidget(self.table, alignment=Qt.AlignTop)
        self.layout.addStretch()
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        # 💡 テーブル単一行の高さを計算
        # QTableWidgetの行高さを取得するため、一時的に行を追加して測定する
        self.table.insertRow(0)
        self.table.resizeRowsToContents()
        self._single_row_height = self.table.rowHeight(0)
        self._table_header_height = self._single_row_height
        self.table.removeRow(0) # ダミー行を削除
        
        # Widgetのリフレッシュ
        self._fix_column_widths_based_on_contents()
        self._fix_height_based_on_contents()

        self.setStyleSheet(f"#AccountFrame {{ border: 0px solid #333366; background-color: {self.header_color}; border-radius:0px; }}")
        self.adjustSize() 

    # ----------------------------------------------------
    # マウスイベントハンドラ (フローティング/ドラッグ機能)
    # ----------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        """マウスの左ボタンが押されたとき、ドラッグ開始位置を記録しカーソルを変更"""
        if not self.enable_drag:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.position().toPoint() 
            self.setCursor(Qt.ClosedHandCursor) # 掴んでいるカーソルに変更
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """マウスが移動したとき、ウィンドウを移動させる"""
        if not self.enable_drag:
            super().mouseMoveEvent(event)
            return

        if self._drag_start_position is not None:
            # ウィジェットの新しいグローバル位置から、ドラッグ開始時のローカル位置を引く
            new_global_pos = event.globalPosition().toPoint() - self._drag_start_position 
            
            # 親ウィジェットの子ウィジェットを取得
            parent_widget = self.parent()
            if parent_widget:
                # 自身と同じ型の兄弟ウィジェットを取得
                all_widgets = parent_widget.findChildren(AccountEntryWidget)
                
                # 💡 スナップ処理を呼び出す
                snapped_pos = self._check_snap(new_global_pos, all_widgets)
                self.move(snapped_pos)
            else:
                self.move(new_global_pos)
            
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウスボタンが離されたとき、ドラッグ状態を解除しカーソルを元に戻す"""
        if not self.enable_drag:
            super().mouseReleaseEvent(event)
            return

        if event.button() == Qt.LeftButton:
            self._drag_start_position = None
            self.setCursor(Qt.OpenHandCursor) # 元のカーソルに戻す
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        if not self.enable_drag:
            super().enterEvent(event)
            return

        self.setStyleSheet(f"#AccountFrame {{background-color: #FFFACD; border: 0px solid #333366; border-radius: 0px;}}")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.enable_drag:
            super().leaveEvent(event)
            return

        self.setStyleSheet(f"#AccountFrame {{background-color: {self.header_color}; border: 0px solid #333366; border-radius: 0px;}}")
        super().leaveEvent(event)


    # ----------------------------------------------------
    # 💡 【新規】スナップ判定ロジック
    # ----------------------------------------------------
    def _check_snap(self, current_pos: QPoint, all_widgets: list['AccountEntryWidget']) -> QPoint:
        """現在の位置を周囲のウィジェットにスナップさせるか判定する"""
        
        # 現在のウィジェットの幅と高さ
        current_rect = self.geometry()
        snapped_x = current_pos.x()
        snapped_y = current_pos.y()

        # 現在のウィジェットの辺の座標（親ウィジェットに対するローカル座標）
        current_left = current_pos.x()
        current_right = current_pos.x() + current_rect.width()
        current_top = current_pos.y()
        current_bottom = current_pos.y() + current_rect.height()
        current_center_x = current_left + current_rect.width() / 2
        current_center_y = current_top + current_rect.height() / 2

        # 自身を除くすべてのウィジェットとチェック
        for other in all_widgets:
            if other is self or other.isHidden():
                continue
            
            other_rect = other.geometry()
            other_left = other_rect.x()
            other_right = other_rect.x() + other_rect.width()
            other_top = other_rect.y()
            other_bottom = other_rect.y() + other_rect.height()
            other_center_x = other_left + other_rect.width() / 2
            other_center_y = other_top + other_rect.height() / 2
            
            # --- 水平方向のスナップ判定 (X軸) ---
            
            # 1. 左辺 vs 右辺 (自分の左が相手の右にスナップ)
            if abs(current_left - other_right) <= self.SNAP_DISTANCE:
                snapped_x = other_right
            # 2. 右辺 vs 左辺 (自分の右が相手の左にスナップ)
            elif abs(current_right - other_left) <= self.SNAP_DISTANCE:
                snapped_x = other_left - current_rect.width()
            # 3. 左辺 vs 左辺 (自分の左が相手の左にスナップ)
            elif abs(current_left - other_left) <= self.SNAP_DISTANCE:
                snapped_x = other_left
            # 4. 右辺 vs 右辺 (自分の右が相手の右にスナップ)
            elif abs(current_right - other_right) <= self.SNAP_DISTANCE:
                snapped_x = other_right - current_rect.width()
            # 5. 中央 vs 中央 (X軸中央揃え)
            elif abs(current_center_x - other_center_x) <= self.SNAP_DISTANCE:
                snapped_x = int(other_center_x - current_rect.width() / 2)


            # --- 垂直方向のスナップ判定 (Y軸) ---
            
            # 1. 上辺 vs 下辺 (自分の上が相手の下にスナップ)
            if abs(current_top - other_bottom) <= self.SNAP_DISTANCE:
                snapped_y = other_bottom
            # 2. 下辺 vs 上辺 (自分の下が相手の上にスナップ)
            elif abs(current_bottom - other_top) <= self.SNAP_DISTANCE:
                snapped_y = other_top - current_rect.height()
            # 3. 上辺 vs 上辺 (自分の上が相手の頭にスナップ)
            elif abs(current_top - other_top) <= self.SNAP_DISTANCE:
                snapped_y = other_top
            # 4. 下辺 vs 下辺 (自分の下が相手の下にスナップ)
            elif abs(current_bottom - other_bottom) <= self.SNAP_DISTANCE:
                snapped_y = other_bottom - current_rect.height()
            # 5. 中央 vs 中央 (Y軸中央揃え)
            elif abs(current_center_y - other_center_y) <= self.SNAP_DISTANCE:
                snapped_y = int(other_center_y - current_rect.height() / 2)
                
        return QPoint(snapped_x, snapped_y)

    # ----------------------------------------------------
    # アイテム追加関数
    # ----------------------------------------------------
    def get_minimum_height(self):
        return self._single_row_height + self._table_header_height

    def get_needed_height(self):
        """現在の行数に基づいてテーブルとウィジェットの必要な高さを返す。"""
        
        margin = 8
        h = self.header_label.height() + margin

        rows = self.table.rowCount()
        for i in range(rows):
            h += self._single_row_height
                
        return h


    def add_item(self, item_name: str, amount: int):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # ---- 勘定科目 ----
        item = QTableWidgetItem(item_name)
        item.setFont(self.font)
        self.table.setItem(row, 0, item)

        # ---- 金額 ----
        amount_item = QTableWidgetItem(f"{amount:,} ")
        amount_item.setFont(self.font)
        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 1, amount_item)

        self.table.setRowHeight(row, self._single_row_height)
        #self.table.resizeRowsToContents() # 内容に合わせて行高さを調整
        self._fix_column_widths_based_on_contents()
        
        # 💡 【追加】高さを固定する関数を呼び出す
        self._fix_height_based_on_contents() 
        
        # 💡 アイテム追加後、ウィジェット全体のサイズを内容に合わせて調整
        self.adjustSize() 

    def _find_item_and_amount(self, item_name: str) -> Tuple[int, Optional[int]]:
        """
        テーブル内で勘定科目名 (列0) を検索し、
        見つかった場合はその行インデックスと列1 (金額) の数値を返す。
        見つからない場合は (-1, None) を返す。
        """
        for row in range(self.table.rowCount()):
            # 1. 勘定科目名 (列0) をチェック
            name_item = self.table.item(row, 0)
            if name_item and name_item.text() == item_name:
                # 2. 勘定科目が見つかった場合、金額 (列1) を取得
                amount_item = self.table.item(row, 1)
                
                amount_value: Optional[int] = None
                if amount_item:
                    try:
                        # テキストからカンマ(,)とスペース( )を取り除き、整数に変換
                        text_value = amount_item.text().replace(',', '').strip()
                        amount_value = int(text_value)
                    except ValueError:
                        # 変換エラーが発生した場合は None のまま
                        pass
                
                # 行インデックスと金額を返す
                return row, amount_value
                
        # 見つからなかった場合
        return -1, None

    def update_item(self, item_name: str, amount: int):
        """
        テーブルに勘定項目があれば金額を比較し、異なれば更新する。なければ新規追加する。
        """
        # 1. 統合されたメソッドで検索と金額取得を同時に行う
        row_index, existing_amount = self._find_item_and_amount(item_name)

        if row_index != -1:
            # 2. 既存の場合: 金額を比較
            
            # 🌟 変更点: 金額が一致するかチェック 🌟
            if existing_amount == amount:
                logger.debug(f"Skip: {item_name} の金額は {amount:,} で一致しているため、更新をスキップしました。")
                return # 一致する場合は処理を終了
            
            # 金額が異なる場合、更新を実行
            
            # ---- 金額 ----
            amount_text = f"{amount:,} "
            amount_item = QTableWidgetItem(amount_text)
            
            # 既存の行の列1（金額）を新しいアイテムで上書き
            amount_item.setFont(self.font)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 1, amount_item)
            
            # 高さ・幅・ウィジェットサイズ調整の呼び出し
            self.table.setRowHeight(row_index, self._single_row_height) 
            self._fix_column_widths_based_on_contents()
            self._fix_height_based_on_contents() 
            self.adjustSize()
            
            logger.debug(f"Update: {item_name} の金額を {existing_amount:,} -> {amount:,} に更新しました。")
        else:
            # 3. 存在しない場合: add_item を呼び出して新しい行を追加
            self.add_item(item_name, amount)
            logger.debug(f"Add: {item_name} を新規追加し、金額 {amount:,} を設定しました。")

    def clear_all(self):
        self.table.setRowCount(0)

    def get_all_items(self) -> list[tuple[str,int]]:
        """
        テーブル内のすべてのアイテムを [(item_name, amount), ...] で返す
        """
        items = []
        row_count = self.table.rowCount()
        for row in range(row_count):
            name_item = self.table.item(row, 0)
            amount_item = self.table.item(row, 1)
            if name_item and amount_item:
                name = name_item.text()
                amount_text = amount_item.text().replace(',', '')
                try:
                    amount = int(amount_text)
                except ValueError:
                    amount = 0
                items.append((name, amount))
        return items
        
    def get_total_amount(self) -> int:
        """
        テーブルの2列目（金額）に表示されているすべての項目の合計値を計算して返します。
        
        QTableWidgetItemのテキストからカンマや通貨単位の書式を削除し、整数に変換して合計します。
        """
        total = 0
        amount_column = 1  # 金額は2列目（インデックス1）
        
        # テーブルの全行を反復処理
        for row in range(self.table.rowCount()):
            item = self.table.item(row, amount_column)
            
            if item is not None:
                amount_text = item.text().strip()  # 前後の空白を削除
                
                # 💡 書式を削除し、金額を数値として抽出
                # 例: "120,000 " -> "120000"
                cleaned_amount_text = amount_text.replace(",", "")
                
                try:
                    amount = int(cleaned_amount_text)
                    total += amount
                except ValueError:
                    # 変換エラーが発生した場合（データが予期しない形式の場合）
                    logger.debug(f"警告: 行 {row} の金額 '{amount_text}' を数値に変換できませんでした。")
                    continue
        
        return total

    def get_max_column_width(self) -> int:
        """
        テーブルの内容全体に基づき、2列で統一するために必要な最大の列幅を計算して返します。
        
        このメソッドは、実際のウィジェットの幅設定は行いません。
        戻り値は、統一された1列あたりの必要な幅 (unified_width) です。
        """
        rows = self.table.rowCount()
        min_widths = [0, 0]

        # 各列の最大幅を計算
        for col in range(2):
            needed_width = 20  # ベースとなる最小幅

            for row in range(rows):
                item = self.table.item(row, col)
                if item:
                    # 文字列の幅を計算し、マージン (20) を追加
                    w = self.fm.horizontalAdvance(item.text()) + 20
                    needed_width = max(needed_width, w)

            min_widths[col] = needed_width

        # 2列のうち、より広い方の幅を採用して統一列幅とする
        unified_width = max(min_widths)

        return unified_width

    def set_fixed_column_width(self, unified_width: int):
        """
        QTableWidgetの2列に対し、計算された統一幅を適用し、固定します。
        """
        # 💡 スクロールバーが常にオフになっているため、ここではスクロールバー幅の考慮は不要
        self.table.setColumnWidth(0, unified_width)
        self.table.setColumnWidth(1, unified_width)

        # 1. テーブルの総幅を正確に計算する
        table_width_needed = (unified_width * 2)
        
        # 2. QTableWidgetとQLabelに幅を固定または最小幅を設定
        self.table.setMinimumWidth(table_width_needed) 
        
        # 💡 QLabelの幅を強制的にテーブルの幅に合わせる
        self.header_label.setFixedWidth(table_width_needed) 
        
        # 💡 AccountEntryWidget全体の幅を固定する (ユーザー要求を維持)
        # ※この行があると、幅のサイズ変更はできなくなります
        self.setFixedWidth(table_width_needed + 8) 
        
        # 3. 親ウィジェットに最小サイズへの調整を強制
        self.adjustSize()

    # ----------------------------------------------------
    # 内容に基づき列幅を最小化し、2列同じ幅で固定
    # ----------------------------------------------------
    def _fix_column_widths_based_on_contents(self):
        unified_width = self.get_max_column_width()
        self.set_fixed_column_width(unified_width)

    # ----------------------------------------------------
    # 【追加】現在の行数に基づいて高さを最小化
    # ----------------------------------------------------
    def _fix_height_based_on_contents(self):
        """現在の行数に基づいてテーブルとウィジェットの高さを調整する"""
        
        rows = self.table.rowCount()
        self.header_label.setFixedHeight(self._table_header_height) 

        table_needed_height = 0
        if rows > 0:
            for i in range(rows):
                table_needed_height += self._single_row_height
                
        self.table.setMinimumHeight(0)
        self.table.setMaximumHeight(table_needed_height) 
        self.setFixedHeight(self._table_header_height + table_needed_height + 10) 

        self.adjustSize()


# --------------------------------------------------------
# 動作テスト
# --------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 💡 main_widgetを一般的なコンテナとして設定
    main_widget = QWidget()
    main_widget.setWindowTitle("Main Container (Floater Test)")
    # 💡 初期サイズを適切に設定
    main_widget.setGeometry(0, 0, 10, 10)
    main_widget.setStyleSheet("background-color: #F0F0F0;")
    
    # font = QFont("Meiryo", 10)
    font = QFont("MS Gothic", 10)
    

    # 💡 AccountEntryWidgetをmain_widgetの子としてインスタンス化
    w1 = AccountEntryWidget(main_widget, "資産", font, "#e0e0ff")
    w2 = AccountEntryWidget(main_widget, "負債", font, "#e0e0ee")
    w3 = AccountEntryWidget(main_widget, "純資産", font, "#e0e0dd")

    # テストデータ
    w1.add_item("現金", 120000)
    w1.add_item("売掛金", 35000000000)
    w1.add_item("普通預金", 445500)
    w1.add_item("事務用品費", 2300)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("旅費交通費", 8000)
    w1.add_item("事務用品費", 2300)
    
    w2.add_item("買掛金", 150000)
    w2.add_item("短期借入金", 5000000)
    #w2.add_item("未払金", 75000)
    
    w3.add_item("資本金", 150000)
    #w3.add_item("資本剰余金", 150000)

    # 初期位置設定
    w1.move(50, 50)
    w2.move(w1.width() + 100, 50)
    w3.move(w1.width() + 100 + w2.width() + 100, 50)

    col_width = w1.get_max_column_width()
    w2.set_fixed_column_width(col_width)
    w3.set_fixed_column_width(col_width)

    w1.show()
    w2.show()
    w3.show()

    logger.debug(f"w1 : {w1.get_total_amount()}")
    logger.debug(f"w2 : {w2.get_total_amount()}")
    logger.debug(f"w3 : {w3.get_total_amount()}")

    main_widget.show()

    sys.exit(app.exec())