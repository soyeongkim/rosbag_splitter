
# Rosbag Splitter GUI

This application provides a graphical user interface for splitting ROS bag files into smaller segments based on the selected topics and size limits.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed Python 3.
- You have installed ROS (Robot Operating System).
- You have installed the following Python packages:

```bash
pip install PyQt5
pip install rospkg
pip install catkin_pkg
```

## Installing

1. **Clone the repository:**

   ```bash
   git clone https://github.com/soyeongkim/rosbag_splitter.git
   cd rosbag_splitter
   ```

## Usage

1. **Run the application:**

   ```bash
   python bag_splitter_gui.py
   ```

2. **Using the GUI:**

   - **Select Input Bag:** Click the "Select Input Bag" button to choose the input ROS bag file.
   - **Select Topics:** The list of topics in the selected bag file will be displayed. You can choose which topics to include in the output files.
   - **Set Size Limit (Optional):** Check the "Size Limit" checkbox and specify the maximum size in MB for each output bag file.
   - **Start Splitting:** Click the "Split" button to start splitting the bag file.
   - **Stop Splitting:** Click the "Stop" button to stop the splitting process.

## Notes

- The application will log the progress and status of the splitting process in the log output area.
- Ensure that the output file is not the same as the input file to avoid overwriting data.
