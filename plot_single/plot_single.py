import pandas as pd
import matplotlib.pyplot as plt
import yaml
import os
import sys

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def clean_column_names(columns, cleanup_rules):
    cleaned = []
    for col in columns:
        for rule in cleanup_rules:
            col = col.replace(rule, "")
        cleaned.append(col.strip())
    return cleaned


def ms_to_seconds(ms):
    return ms / 1000.0

def print_usage():
    print("""
Usage:
    python plot_single.py <config.yaml>

Description:
    This script reads a CSV file and plots selected columns based on settings in a YAML config file.

Available Configuration Options in config.yaml:
    input_file:           Path to the input CSV file (e.g., input/data.csv)
    plot_size:            Plot dimensions in inches [width, height] (e.g., [10, 6])
    font_sizes:
        title:            Font size for the plot title
        legend:           Font size for the legend
        axis:             Font size for axis labels
    columns_to_plot:      List of column indices to plot (excluding time/sample column).
                         Use [] or omit to plot all available columns.
    sampling_rate_ms:     Sampling interval in milliseconds (e.g., 100)
    time_window:          Time range to display [start_s, end_s] in seconds.
                         Leave empty or omit to plot full range.
    header_cleanup:       List of substrings to remove from column headers (e.g., ["Ave. (C)", "(C)"])
    save_formats:         Output formats to save the plot (e.g., ["jpeg", "pdf"] or []  to skip saving)
    output_dir:           Optional. Directory to save output files. Defaults to "output/"

Example:
    python plot_single.py config.yaml
""")

def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("--help", "-h"):
        print_usage()
        return

    config_file = sys.argv[1]
    config = load_config(config_file)

    # Load CSV
    df = pd.read_csv(config["input_file"])
    cleanup_rules = config.get("header_cleanup", [])
    df.columns = clean_column_names(df.columns, cleanup_rules)

    # Time axis
    sampling_rate = ms_to_seconds(config.get("sampling_rate_ms", 100))
    time = [i * sampling_rate for i in range(len(df))]

    # Time window
    time_window = config.get("time_window", [])
    if time_window:
        start_s, end_s = time_window
        start_idx = int(start_s / sampling_rate)
        end_idx = int(end_s / sampling_rate)
    else:
        start_idx = 0
        end_idx = len(time)

    time_windowed = time[start_idx:end_idx]

    # Column selection
    all_columns = df.columns[1:]  # skip first column (sample number)
    selected_indices = config.get("columns_to_plot", [])
    if not selected_indices:
        selected_indices = list(range(len(all_columns)))
    selected_columns = [all_columns[i] for i in selected_indices]

    # Plot setup
    plt.figure(figsize=tuple(config.get("plot_size", [10, 6])))

    for col in selected_columns:
        plt.plot(time_windowed, df[col][start_idx:end_idx], label=col)

    # Fonts
    fonts = config.get("font_sizes", {})
    plt.xlabel("Time (s)", fontsize=fonts.get("axis", 12))
    plt.ylabel("Value", fontsize=fonts.get("axis", 12))
    plt.title("CSV Plot", fontsize=fonts.get("title", 14))
    plt.legend(fontsize=fonts.get("legend", 10))
    plt.tight_layout()
    plt.xlim(time_windowed[0], time_windowed[-1])
    plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)

    # Save outputs
    filename = os.path.splitext(os.path.basename(config["input_file"]))[0]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    for fmt in config.get("save_formats", []):
        plt.savefig(f"{output_dir}/{filename}.{fmt}", format=fmt)

    plt.show()

if __name__ == "__main__":
    main()
