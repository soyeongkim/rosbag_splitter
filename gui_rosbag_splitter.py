import sys
import os
import copy
import rosbag
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QListWidget, QTextEdit, QLineEdit, QLabel, QProgressBar, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class BagSplitterThread(QThread):
    progress_update = pyqtSignal(float)
    log_update = pyqtSignal(str)
    finish_signal = pyqtSignal(bool)

    def __init__(self, input_bag_file, output_bag_file_name, max_size_bytes, selected_topics):
        super().__init__()
        self.bag = input_bag_file
        self.output_bag_file_name = output_bag_file_name
        self.max_size_bytes = max_size_bytes
        self.selected_topics = selected_topics
        self.stop_signal = False
        
    def __del__(self):
        if self.bag is not None:
            self.bag.close()

    def run(self):
        try:
            self.log_update.emit(f"Splitting bag...")
            
            # Display selected topics in log with new line and hipone indent
            self.log_update.emit(f"Selected topics:")
            for topic in self.selected_topics:
                self.log_update.emit(f"  - {topic}")

            # Remove file if it exists
            if os.path.exists(self.output_bag_file_name):
                os.remove(self.output_bag_file_name)

            # Remove extension
            self.output_bag_file_name = self.output_bag_file_name.rsplit('.', 1)[0]

            # Display output path
            self.log_update.emit(f"Output path: {self.output_bag_file_name}")

            # Display max size
            limit_size = False
            if(self.max_size_bytes <= 0):
                self.log_update.emit(f"No size limit")
                limit_size = False
            else:
                self.log_update.emit(f"Max size: {self.max_size_bytes / (1024 * 1024)} MB")
                limit_size = True

            split_count = 0
            topic_count = 0
            output_bag = None
            output_bag_size = 0

            # Reset position of bag
            self.progress_update.emit(0)
            for topic, msg, t in self.bag.read_messages():
                if self.stop_signal:
                    self.log_update.emit("Stopping...")
                    if output_bag is not None:
                        output_bag.close()
                    break
        
                # Progress display
                topic_count += 1
                progress = float(topic_count / self.bag.get_message_count() * 100)
                self.progress_update.emit(progress)

                # Save the bag if it is not created yet
                if output_bag is None:
                    if limit_size == True:
                        output_bag_path = f"{self.output_bag_file_name}_{split_count:03d}.bag"
                    else:
                        output_bag_path = self.output_bag_file_name + ".bag"
                        
                    # Remove file if it exists
                    if os.path.exists(output_bag_path):
                        os.remove(output_bag_path)
                        
                    # Create new bag
                    output_bag = rosbag.Bag(output_bag_path, 'w')
                    self.log_update.emit(f"Creating new bag: {output_bag_path}")
                    output_bag_size = 0

                # Write the message to the bag
                if topic in self.selected_topics:
                    output_bag.write(topic, msg, t)
                    output_bag_size = os.path.getsize(output_bag_path)
            
                # Close the bag if it is full
                if limit_size == True and output_bag_size >= self.max_size_bytes:
                    output_bag.close()
                    self.log_update.emit(f"Closed bag: {output_bag_path} with size: {output_bag_size / (1024 * 1024)} MB")
                    split_count += 1
                    output_bag = None

            if output_bag is not None:
                output_bag.close()
                self.log_update.emit(f"Closed bag: {output_bag_path} with size: {output_bag_size / (1024 * 1024)} MB")

            # Display completion message
            self.log_update.emit("Completed splitting bag.")
            
            # Display result
            self.log_update.emit(f"Result: {split_count + 1} bags created.")
            self.finish_signal.emit(True)
        except Exception as e:
            self.log_update.emit(f"Error occurred while splitting bag: {str(e)}")
            self.finish_signal.emit(False)

    def stop(self):
        self.stop_signal = True

class BagSplitterGUI(QWidget):
    def __init__(self):
        super().__init__()
        
        self.bag = None
        self.file_size_GB = 0
        self.splitter_thread = None
        self.input_bag = None
        self.output_bag_file_name = None
        self.max_size_bytes = 0
        self.selected_topics = []
        
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
        self.max_size_input.textChanged.connect(self.determine_estimated_file_count)
        self.max_size_input.setText('500')
        self.max_size_input.setEnabled(False)
        size_layout.addWidget(self.max_size_input)
        layout.addLayout(size_layout)

        # Split button and estimated file count
        split_layout = QHBoxLayout()
        self.split_button = QPushButton('Split')
        self.split_button.setEnabled(False)
        self.split_button.clicked.connect(self.start_splitting)
        split_layout.addWidget(self.split_button)
        self.stop_button = QPushButton('Stop')
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_splitting)
        split_layout.addWidget(self.stop_button)
        self.estimated_files_label = QLabel('Estimated File Count: 0')
        split_layout.addWidget(self.estimated_files_label)
        layout.addLayout(split_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100*100)
        
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        
        self.setWindowTitle('Rosbag Splitter')
        self.resize(900, 675) # Default size: 900x675
        self.show()
        
    def clear_data(self):
        # Clear data
        self.file_size_GB_ = 0
        self.bag = None
        self.input_bag = None
        self.selected_topics = []
        
        # Clear selected topics
        self.topic_list.clear()
        
        # Disable split button
        self.split_button.setEnabled(False)
        

    def toggle_all_topics(self):
        if self.select_all_checkbox.isChecked():
            self.topic_list.selectAll()
        else:
            self.topic_list.clearSelection()

    def select_input_bag(self):
        # Clear things
        self.clear_data()
        
        # Select file
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Input Bag', '', 'Bag Files (*.bag)')
        self.log_output.append(f'Selected Input Bag: {file_name}')
        if file_name:
            self.file_size_GB = os.path.getsize(file_name) / (1024 * 1024 * 1024)  # Convert to GB
            if self.file_size_GB >= 1:
                self.log_output.append(f'File size is {self.file_size_GB:.2f}GB. It may take some time to read the topic list.')
            self.determine_estimated_file_count()
            self.log_output.append('Loading topic list...')
            QApplication.processEvents()
            self.input_bag = file_name
            self.load_topics()
            self.split_button.setEnabled(True)
        else:
            self.log_output.append('Please select an input bag file.')

    def load_topics(self):
        # Load topic list from the selected bag file and display in topic_list.
        if self.input_bag:
            try:
                if(self.bag is not None):
                    self.bag.close()
                self.bag = rosbag.Bag(self.input_bag, 'r')
                topics = self.bag.get_type_and_topic_info()[1].keys()
                self.topic_list.clear()
                for topic in topics:
                    self.topic_list.addItem(topic)
                self.log_output.append(f'Successfully loaded topic list. Total topics: {len(topics)}')
                self.topic_list.selectAll()
            except Exception as e:
                self.log_output.append(f'Error occurred while loading topic list: {str(e)}')
        else:
            self.log_output.append('Please select an input bag file first.')
        pass

    def start_splitting(self):
        # Disable split button
        self.split_button.setEnabled(False)
        
        # Select output file
        output_file, _ = QFileDialog.getSaveFileName(self, 'Select Output Bag File', '', 'Bag Files (*.bag)')
        
        # Check if output file is same as input file
        if output_file == self.input_bag:
            self.log_output.append('Output file cannot be the same as input file.')
            self.split_button.setEnabled(True)
            return

        # Check if output file is selected
        if output_file:
            max_size = int(self.max_size_input.text()) * 1024 * 1024  # Convert MB to bytes
            limit_size = self.size_limit_checkbox.isChecked()
            if(limit_size == False):
                max_size = 0
            selected_topics = [item.text() for item in self.topic_list.selectedItems()]

            self.splitter_thread = BagSplitterThread(self.bag, output_file, max_size, selected_topics)
            self.splitter_thread.progress_update.connect(self.update_progress)
            self.splitter_thread.log_update.connect(self.update_log)
            self.splitter_thread.finish_signal.connect(self.finish_splitting)
            self.splitter_thread.start()
            self.stop_button.setEnabled(True)
        else:
            self.log_output.append('Please select an output bag file.')
            self.stop_button.setEnabled(True)
    
    def stop_splitting(self):
        if self.splitter_thread is not None:
            self.splitter_thread.stop()
            # Join the thread
            self.splitter_thread.wait()
            self.stop_button.setEnabled(False)
            if(self.bag is not None):
                self.split_button.setEnabled(True)
                
    def finish_splitting(self, status):
        if status == True:
            self.log_output.append("Completed splitting bag.")
            self.split_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            # currently re-split is not supported
            self.bag.close()
            self.bag = None
            self.split_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            # Clear
            self.clear_data()
        else:
            self.log_output.append("Failed to split bag.")
            self.split_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            # Clear
            self.clear_data()
            
    
    def determine_estimated_file_count(self):
        if(self.file_size_GB == 0):
            self.log_output.append('Please select an input bag file first.')
            return
        if(self.max_size_input.text() == ""):
            self.estimated_files_label.setText(f'Estimated File Count: 0')
            return
        file_size_MB = self.file_size_GB * 1024
        try:
            if(self.size_limit_checkbox.isChecked() == False):
                self.estimated_files_label.setText(f'Estimated File Count: 1')
            else:
                max_size_MB = int(self.max_size_input.text())
                estimated_file_count = file_size_MB / max_size_MB
                self.estimated_files_label.setText(f'Estimated File Count: {estimated_file_count:.0f}')
        except Exception as e:
            self.log_output.append(f'Error occurred while determining estimated file count: {str(e)}')

    def toggle_size_limit(self):
        self.max_size_input.setEnabled(self.size_limit_checkbox.isChecked())

    def update_progress(self, value):
        self.progress_bar.setMaximum(100 * 100)
        self.progress_bar.setValue(value * 100)
        self.progress_bar.setFormat("%.02f %%" % value)
        # self.progress_bar.setValue(int(value))

    def update_log(self, message):
        self.log_output.append(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BagSplitterGUI()
    ex.show()
    
    sys.exit(app.exec_())