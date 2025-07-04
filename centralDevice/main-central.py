from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget
from pyqtgraph import PlotWidget, mkPen
import asyncio
import sys
import random

class CoffeeRoasterMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coffee Roaster Monitor")
        self.setGeometry(100, 100, 800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout
        
        self.graph_widget = PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.setLabel('left', 'Temperature (F)')
        self.graph_widget.setLabel('bottom', 'Time (s)')
        
        self.temp1_curve = self.graph_widget.plot([], [], pen=mkPen(color='r', width=2), name="Temp 1")
        self.temp2_curve = self.graph_widget.plot([], [], pen=mkPen(color='b', width=2), name="Temp 2")
        
        layout.addWidget(self.graph_widget)
        
        self.start_button = QPushButton("Start Logging")
        self.stop_button = QPushButton("Stop Logging")
        self.save_button = QPushButton("Save Data")
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.save_button)
        
        self.start_button.clicked.connect(self.start_logging)
        self.stop_button.clicked.connect(self.stop_logging)
        self.save_button.clicked.connect(self.save_data)
        
        self.data_x = []  # Time axis
        self.data_temp1 = []  # Temperature 1 data
        self.data_temp2 = []  # Temperature 2 data
        self.running = False
        
        self.update_timer = self.startTimer(1000)  # 1-second update interval
    
    def timerEvent(self, event):
        if self.running:
            new_time = len(self.data_x)
            temp1 = random.uniform(200, 400)  # Placeholder for real temp data
            temp2 = random.uniform(200, 400)  # Placeholder for real temp data
            
            self.data_x.append(new_time)
            self.data_temp1.append(temp1)
            self.data_temp2.append(temp2)
            
            self.temp1_curve.setData(self.data_x, self.data_temp1)
            self.temp2_curve.setData(self.data_x, self.data_temp2)
    
    def start_logging(self):
        self.running = True
    
    def stop_logging(self):
        self.running = False
    
    def save_data(self):
        with open("roast_log.txt", "w") as f:
            for t, temp1, temp2 in zip(self.data_x, self.data_temp1, self.data_temp2):
                f.write(f"{t},{temp1},{temp2}\n")
        print("Data saved to roast_log.txt")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoffeeRoasterMonitor()
    window.show()
    sys.exit(app.exec())
