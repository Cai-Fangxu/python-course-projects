import sys
import requests
from bs4 import BeautifulSoup as BSoup
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie, QFont


# This class is used to crawl and show data related to football news
class FootballNews:
    def __init__(self):
        self.response = requests.get("https://m.dongqiudi.com/home/104")
        self.response.encoding = 'utf-8'
        self.raw_list = BSoup(self.response.text, features="lxml").ul.find_all('li')
        # In the website's html source code, news' entries are contained in 'li' tags
        self.news_list = []  # used to store titles and links of reports
        # note that not all reports are game reports
        self.game_report_title = []
        self.game_report_idx = []  # used to store the index of game reports in self.news_list
        self.game_report_content = []

        # get the title and link of every piece of news
        for tag in self.raw_list:
            try:
                self.news_list.append([tag.h3.contents[0], tag.a['href']])
            except Exception:
                pass

        self.FindGameReport()

    # This method is used to find game reports from all the crawled reports
    # A report is a game report if its title contains a string like "XX-XX", where "XX" is the score
    def FindGameReport(self):
        num_list = '0123456789'
        for idx, entry in enumerate(self.news_list):
            score_pos = entry[0].find('-')
            if score_pos != -1 and entry[0][score_pos - 1] in num_list and entry[0][score_pos + 1] in num_list:
                self.game_report_title.append(entry)
                self.game_report_idx.append(idx)

    # This method crawls football commentary and key moments gif images from a game report web page
    def GetGameDetails(self, game_report_url):
        self.game_report_content = []
        response = requests.get(game_report_url)
        response.encoding = 'utf-8'
        soup = BSoup(response.text, features="lxml")

        # if the web page doesn't contain a subtitle called '关键事件', it's not a football game web page
        try:
            if soup.h2.string != '关键事件':
                return -1
        except Exception:
            return -1

        # crawl data related to key moments
        for sibling in soup.h2.next_siblings:
            if sibling.name == 'h2':
                break
            self.game_report_content.append(sibling)
            # data stored in game_report_content needs further processing

        for idx, item in enumerate(self.game_report_content):
            if item.img:
                # if item has image tag, download gif and set item to 'gif'
                try:
                    gif_url = item.img['data-gif-src']
                except Exception:
                    # an exception might occur if the image is just an advertisement
                    self.game_report_content[idx] = 0
                    continue
                if gif_url.find('?'):
                    gif_url = gif_url[:gif_url.find('?')]
                gif = requests.get(gif_url).content
                with open('{}.gif'.format(idx), 'wb') as f:
                    f.write(gif)
                    f.close()
                self.game_report_content[idx] = 'gif'
            elif item.strings:
                # if item has strings, they are football commentary
                self.game_report_content[idx] = ''.join(item.strings)
            else:
                pass

    # used to display news in a window
    def MakeWindow(self):
        self.my_window = QWidget()
        self.whole_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        left_widget = QWidget()
        right_widget = QWidget()
        left_widget.setLayout(self.left_layout)
        right_widget.setLayout(self.right_layout)
        self.whole_layout.addWidget(left_widget)
        self.whole_layout.addWidget(right_widget)
        self.my_window.setLayout(self.whole_layout)

        # construct the left side of the window, display a list of news
        self.ShowNewsList()

        # construct the right side of the window, it'll be empty at this point
        self.right_scroll_area = QScrollArea()
        self.right_scroll_widget = QWidget()
        self.right_scroll_widget.setMinimumSize(800, 1500)
        scroll_layout = QVBoxLayout()
        scroll_layout.setAlignment(Qt.AlignHCenter)
        self.right_scroll_widget.setLayout(scroll_layout)
        self.right_scroll_area.setWidget(self.right_scroll_widget)
        self.right_layout.addWidget(self.right_scroll_area)

        return self.my_window

    # construct the left side of the window, display a list of news
    def ShowNewsList(self):
        # make top label
        left_label0 = QLabel()
        left_label0.setText("What's New?\nFootball News and Other!")
        left_label0.setAlignment(Qt.AlignCenter)
        left_label0.setWordWrap(True)
        self.left_layout.addWidget(left_label0)

        # make a scroll area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setMinimumSize(800, 70*len(self.news_list))
        scroll_layout = QVBoxLayout()
        scroll_layout.setAlignment(Qt.AlignHCenter)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        self.left_layout.addWidget(scroll_area)

        left_label = [QLabel()]*len(self.news_list)
        for idx, entry in enumerate(self.news_list):
            # every report corresponds to a button, if the report is not a game report, the button is disabled.
            left_label[idx] = QPushButton()
            left_label[idx].setObjectName("{}".format(idx))
            # button's name will be used to identify which button is clicked
            left_label[idx].clicked.connect(self.ButtonClicked)
            left_label[idx].setText(str(idx + 1) + ": " + entry[0])
            scroll_layout.addWidget(left_label[idx])
            left_label[idx].setFixedSize(700, 50)
            if idx not in self.game_report_idx:
                left_label[idx].setFlat(True)
                left_label[idx].setStyleSheet("QPushButton{border: none}")
                left_label[idx].setEnabled(False)
        scroll_layout.addStretch(1)

    # used to display key moments gif and football commentary
    def ShowGameReport(self):
        # clear the right side of the window and then construct it again
        try:
            self.right_scroll_area.deleteLater()
        except Exception:
            pass
        self.right_scroll_area = QScrollArea()
        self.right_scroll_widget = QWidget()
        self.right_scroll_widget.setMinimumSize(800, 350 * len(self.game_report_content))
        scroll_layout = QVBoxLayout()
        scroll_layout.setAlignment(Qt.AlignHCenter)

        self.right_scroll_widget.setLayout(scroll_layout)
        self.right_scroll_area.setWidget(self.right_scroll_widget)
        self.right_layout.addWidget(self.right_scroll_area)

        # put items to the right side of the window
        right_label = [QLabel()]*len(self.game_report_content)
        for idx, item in enumerate(self.game_report_content):
            if item is 'gif':
                gif = QMovie("{}.gif".format(idx))
                gif.setSpeed(125)
                # the speed of gif needs some fine tuning, 125 means 1.25 times original speed
                # the speed gets slower when using original speed
                gif.setScaledSize(QSize(600, 357))
                right_label[idx].setMovie(gif)
                gif.start()
            elif item is 0:
                # this might happen when there's an advertisement image, see method GetNewsDetails
                continue
            else:
                right_label[idx].setText(item)
                right_label[idx].setFont(QFont("Microsoft YaHei", 12))
                right_label[idx].setWordWrap(True)

            right_label[idx].setAlignment(Qt.AlignCenter)
            scroll_layout.addWidget(right_label[idx])
        scroll_layout.addStretch(1)

    # display key moments gif and football commentary of the game of the button clicked
    def ButtonClicked(self):
        # find out which button is clicked
        button = self.my_window.sender()
        idx = int(str(button.objectName()))

        url = self.news_list[idx][1]
        self.GetGameDetails(url)
        self.ShowGameReport()


if __name__ == "__main__":

    temp = FootballNews()
    app = QApplication(sys.argv)
    win = temp.MakeWindow()
    win.show()
    sys.exit(app.exec_())
