import sys
import os
import rosbag
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QListWidget, QTextEdit, QLineEdit, QLabel, QProgressBar, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class BagSplitterThread(QThread):
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)

    def __init__(self, input_bag, output_prefix, max_size, selected_topics):
        super().__init__()
        self.input_bag = input_bag
        self.output_prefix = output_prefix
        self.max_size = max_size
        self.selected_topics = selected_topics

    def run(self):
        # Implement the logic of the split_bag function here.
        # Use progress_update and log_update signals to update progress and logs.
        pass

class BagSplitterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Input bag selection
        self.input_button = QPushButton('Select Input Bag')
        self.input_button.clicked.connect(self.select_input_bag)
        layout.addWidget(self.input_button)

        # Horizontal layout for topic list and log output
        h_layout = QHBoxLayout()

        # Topic list
        topic_layout = QVBoxLayout()
        topic_label = QLabel('Select topics to output:')
        topic_layout.addWidget(topic_label)
        self.select_all_checkbox = QCheckBox('Select/Deselect All')
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_topics)
        topic_layout.addWidget(self.select_all_checkbox)
        self.topic_list = QListWidget()
        self.topic_list.setSelectionMode(QListWidget.MultiSelection)
        topic_layout.addWidget(self.topic_list)
        h_layout.addLayout(topic_layout)

        # Log output
        log_label = QLabel('Log:')
        log_layout = QVBoxLayout()
        log_layout.addWidget(log_label)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        h_layout.addLayout(log_layout)

        layout.addLayout(h_layout)

        # Size limit checkbox and input
        size_layout = QHBoxLayout()
        self.size_limit_checkbox = QCheckBox('Size Limit')
        self.size_limit_checkbox.stateChanged.connect(self.toggle_size_limit)
        size_layout.addWidget(self.size_limit_checkbox)
        size_layout.addWidget(QLabel('Maximum Size (MB):'))
        self.max_size_input = QLineEdit()
        self.max_size_input.setText('500')
        self.max_size_input.setEnabled(False)
        size_layout.addWidget(self.max_size_input)
        layout.addLayout(size_layout)

        # Split button and estimated file count
        split_layout = QHBoxLayout()
        self.split_button = QPushButton('Split')
        self.split_button.clicked.connect(self.start_splitting)
        split_layout.addWidget(self.split_button)
        self.estimated_files_label = QLabel('Estimated File Count: 0')
        split_layout.addWidget(self.estimated_files_label)
        layout.addLayout(split_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setWindowTitle('Rosbag Splitter')
        self.resize(900, 675) # Default size: 900x675
        self.show()

    def toggle_all_topics(self):
        if self.select_all_checkbox.isChecked():
            self.topic_list.selectAll()
        else:
            self.topic_list.clearSelection()

    def select_input_bag(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Input Bag', '', 'Bag Files (*.bag)')
        self.log_output.append(f'Selected Input Bag: {file_name}')
        if file_name:
            file_size = os.path.getsize(file_name) / (1024 * 1024 * 1024)  # Convert to GB
            if file_size >= 1:
                self.log_output.append(f'File size is {file_size:.2f}GB. It may take some time to read the topic list.')
            self.log_output.append('Loading topic list...')
            QApplication.processEvents()
            self.input_bag = file_name
            self.load_topics()

    def load_topics(self):
        # Load topic list from the selected bag file and display in topic_list.
        if self.input_bag:
            try:
                bag = rosbag.Bag(self.input_bag, 'r')
                topics = bag.get_type_and_topic_info()[1].keys()
                self.topic_list.clear()
                for topic in topics:
                    self.topic_list.addItem(topic)
                bag.close()
                self.log_output.append(f'Successfully loaded topic list. Total topics: {len(topics)}')
            except Exception as e:
                self.log_output.append(f'Error occurred while loading topic list: {str(e)}')
        else:
            self.log_output.append('Please select an input bag file first.')
        pass

    def start_splitting(self):
        output_dir = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        if output_dir:
            max_size = int(self.max_size_input.text()) * 1024 * 1024  # Convert MB to bytes
            selected_topics = [item.text() for item in self.topic_list.selectedItems()]
            
            self.splitter_thread = BagSplitterThread(self.input_bag, os.path.join(output_dir, 'split'), max_size, selected_topics)
            self.splitter_thread.progress_update.connect(self.update_progress)
            self.splitter_thread.log_update.connect(self.update_log)
            self.splitter_thread.start()

    def toggle_size_limit(self):
        self.max_size_input.setEnabled(self.size_limit_checkbox.isChecked())

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_output.append(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BagSplitterGUI()
    sys.exit(app.exec_())