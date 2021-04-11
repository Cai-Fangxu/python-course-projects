from utils import *

temp = FootballNews()
app = QApplication(sys.argv)
win = temp.MakeWindow()
win.show()
sys.exit(app.exec_())
