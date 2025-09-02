import sys
import os
import yaml
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import correlate, find_peaks
import numpy as np

def print_usage():
    print("""
Usage:
    python plot_compare.py <config.yaml>

Description:
    This script compares two CSV files by plotting selected columns from both on a single graph.
    The files must have the same number of columns. A warning is shown if column names differ.

Available Configuration Options in config.yaml:
    input_file_1:         Path to the first CSV file (e.g., input/data1.csv)
    input_file_2:         Path to the second CSV file (e.g., input/data2.csv)
    sampling_interval_s_ms:     Sampling interval in milliseconds (e.g., 100)
    time_window:          Time range to display [start_s, end_s] in seconds.
                          Leave empty or omit to plot full range.
    auto_align:           If true, align time series automatically (not yet implemented)
    manual_offset_s:      Time offset in seconds to apply to second file (e.g., 5.0)
    plot_size:            Plot dimensions in inches [width, height] (e.g., [10, 6])
    font_sizes:
        title:            Font size for the plot title
        legend:           Font size for the legend
        axis:             Font size for axis labels
    columns_to_plot:      List of column indices to plot (excluding time/sample column).
                          Use [] or omit to plot all available columns.
    header_cleanup:       List of substrings to remove from column headers (e.g., ["Ave. (C)", "(C)"])
    save_formats:         Output formats to save the plot (e.g., ["jpeg", "pdf"] or [] to skip saving)
    output_dir:           Optional. Directory to save output files. Defaults to "output/"

Example:
    python plot_compare.py config.yaml
""")

def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def clean_column_names(columns, cleanup_rules):
    for rule in cleanup_rules:
        columns = [col.replace(rule, "").strip() for col in columns]
    return columns

def ms_to_seconds(ms):
    return ms / 1000.0

def generate_time_series(length, sampling_interval_s, offset_s=0.0):
    return [(i * sampling_interval_s) + offset_s for i in range(length)]

def validate_structure(df1, df2):
    if len(df1.columns) != len(df2.columns):
        raise ValueError("Column count mismatch between input files.")
    if list(df1.columns) != list(df2.columns):
        print("Warning: Column names do not match exactly.")

def find_rising_edge(signal, slope_threshold):
    # Calculate the difference between consecutive samples
    delta = np.diff(signal)

    # Find the first index where the slope exceeds the threshold
    rising_index = np.argmax(delta > slope_threshold)

    # Since np.diff reduces the array length by 1, adjust the index
    return rising_index + 1


def estimate_offset(df1, df2, sampling_interval_s, selected_columns, config):
    method = config.get("alignment_method", "cross_correlation")  # "cross_correlation" or "peak_detection"
    col1_index = int(config.get("auto_align_column_file1", 1))
    col2_index = int(config.get("auto_align_column_file2", 1))

    if col1_index >= df1.shape[1] or col2_index >= df2.shape[1]:
        raise ValueError(f"Column index out of range. File1: 0–{df1.shape[1]-1}, File2: 0–{df2.shape[1]-1}")

    signal1 = df1.iloc[:, col1_index].values
    signal2 = df2.iloc[:, col2_index].values

    # Normalize
    signal1 = (signal1 - np.mean(signal1)) / np.std(signal1)
    signal2 = (signal2 - np.mean(signal2)) / np.std(signal2)

    if method == "manual":
        offset_s = float(config.get("manual_offset_s", 0.0))
        print(f"[Manual Mode] Using manual offset: {offset_s:.3f} seconds")
        return offset_s
    elif method == "peak_detection":
        return peak_alignment(signal1, signal2, sampling_interval_s)
    else:  # default to rising edge
        return rising_edge_alignment(signal1, signal2, sampling_interval_s)

def rising_edge_alignment(signal1, signal2, sampling_interval_s, slope_threshold=0.1, window_size=200):

    start1 = find_rising_edge(signal1, slope_threshold=0.1)
    start2 = find_rising_edge(signal2, slope_threshold=0.1)
    print(sampling_interval_s)
    offset_s = (start1 -start2) * sampling_interval_s
    print(f"Rising edge found at index {start1} (signal1) and {start2} (signal2)")
    print(f"[Rising-Edge] Estimated offset: {offset_s:.3f} seconds")
    return offset_s

def peak_alignment(signal1, signal2, sampling_interval_s, height=0.5):
    peaks1, _ = find_peaks(signal1, height=height)
    peaks2, _ = find_peaks(signal2, height=height)

    if len(peaks1) == 0 or len(peaks2) == 0:
        print("[Peak Detection] No peaks found — falling back to zero offset.")
        return 0.0

    lag = peaks1[0] - peaks2[0]
    offset_s = lag / sampling_interval_s

    print(f"[Peak Detection] Estimated offset: {offset_s:.3f} seconds")
    return offset_s

def apply_plot_formatting(config):
    plot_format = config.get("plot_format", {})
    fonts = plot_format.get("font_sizes", {})
    
    plt.xlabel(plot_format.get("axis_labels", {}).get("x", "X-AXIS NAME PLACEHOLDER"), fontsize=fonts.get("axis", 14))
    plt.ylabel(plot_format.get("axis_labels", {}).get("y", "Y-AXIS NAME PLACEHOLDER"), fontsize=fonts.get("axis", 14))
    plt.title(plot_format.get("plot_title", "TITLE"), fontsize=fonts.get("title", 16))
    plt.legend(fontsize=fonts.get("legend", 12))

    major = plot_format.get("grid", {}).get("major", {})
    minor = plot_format.get("grid", {}).get("minor", {})
    plt.grid(True, which='major', axis='both', 
            color=major.get("color", "#00000000"),
            linestyle=major.get("linestyle", ":"),
            linewidth=major.get("linewidth", 0.8))
    plt.grid(True, which='minor', axis='both', 
        color=minor.get("color", "#00000000"),
        linestyle=minor.get("linestyle", ":"),
        linewidth=minor.get("linewidth", 0.8))
    
    plt.minorticks_on()
    plt.xticks(fontsize=fonts.get("ticks", 12))
    plt.yticks(fontsize=fonts.get("ticks", 12))

    plt.tight_layout()


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("--help", "-h"):
        print_usage()
        return

    config_file = sys.argv[1]
    config = load_config(config_file)

    file1 = config.get("input_file_1")
    file2 = config.get("input_file_2")
    if not file1 or not file2:
        print("Both input_file_1 and input_file_2 must be specified.")
        return

    cleanup_rules = config.get("header_cleanup", [])
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    df1.columns = clean_column_names(df1.columns, cleanup_rules)
    df2.columns = clean_column_names(df2.columns, cleanup_rules)

    validate_structure(df1, df2)

    sampling_interval_s = ms_to_seconds(config.get("sampling_interval_s_ms", 100))
    sampling_rate = 1 / sampling_interval_s # Samples per second
    auto_align = config.get("alignment_method", False)
    manual_offset_s = config.get("manual_offset_s", 0.0)

    columns = df1.columns[1:]
    selected_indices = config.get("columns_to_plot", [])
    if not selected_indices:
        selected_indices = list(range(len(columns)))
    selected_columns = [columns[i] for i in selected_indices]

    offset_s = estimate_offset(df1, df2, sampling_interval_s, selected_columns, config) if auto_align else manual_offset_s
    print(offset_s)

    time1 = generate_time_series(len(df1), sampling_interval_s)
    time2 = generate_time_series(len(df2), sampling_interval_s, offset_s)


    end_time1 = time1[-1]
    end_time2 = time2[-1]
    max_end_time = min(end_time1, end_time2)

    # Determine time window
    time_window = config.get("time_window", [])
    if time_window:
        start_s, end_s = time_window
        end_s = min(end_s, max_end_time)  # Clamp to available data
    else:
        start_s = 0
        end_s = max_end_time

    # Convert to indices
    start_idx1 = int(start_s / sampling_interval_s)
    end_idx1 = int(end_s / sampling_interval_s)
    start_idx2 = int((start_s - offset_s) / sampling_interval_s)
    end_idx2 = int((end_s - offset_s) / sampling_interval_s)

    # Clamp indices to valid ranges
    end_idx1 = min(end_idx1, len(df1))
    end_idx2 = min(end_idx2, len(df2))
    start_idx1 = max(start_idx1, 0)
    start_idx2 = max(start_idx2, 0)

    # Slice time arrays
    time1_windowed = time1[start_idx1:end_idx1]
    time2_windowed = time2[start_idx2:end_idx2]


    columns = df1.columns[1:]
    selected_indices = config.get("columns_to_plot", [])
    if not selected_indices:
        selected_indices = list(range(len(columns)))
    selected_columns = [columns[i] for i in selected_indices]

    plt.figure(figsize=tuple(config.get("plot_size", [10, 6])))

    for col in selected_columns:
        plt.plot(time1_windowed, df1[col][start_idx1:end_idx1], label=f"{col} (File 1)")
        plt.plot(time2_windowed, df2[col][start_idx2:end_idx2], label=f"{col} (File 2)", linestyle='--')

        # apply formatting
        apply_plot_formatting(config)


    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)
    for fmt in config.get("save_formats", []):
        plt.savefig(f"{output_dir}/comparison_plot.{fmt}", format=fmt)

    plt.show()

if __name__ == "__main__":
    main()
