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

def get_input_files(config):
    # Priority: input_files > input_file > all CSVs in input/
    if "input_files" in config:
        return config["input_files"]
    elif "input_file" in config:
        return [config["input_file"]]
    else:
        return [os.path.join("input", f) for f in os.listdir("input") if f.endswith(".csv")]


def print_usage():
    print("""
Usage:
    python plot_single.py <config.yaml>

Description:
    This script reads one or more CSV files and plots selected columns based on settings in a YAML config file.

Input File Options (choose one):
    input_file:           Path to a single CSV file (e.g., input/data.csv)
    input_files:          List of multiple CSV files to process (e.g., ["input/data1.csv", "input/data2.csv"])
                          If neither is specified, all CSV files in the 'input/' folder will be processed automatically.

Available Configuration Options in config.yaml:
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
    save_formats:         Output formats to save the plot (e.g., ["jpeg", "pdf"] or [] to skip saving)
    output_dir:           Optional. Directory to save output files. Defaults to "output/"
    show_plot:            plot will be displayed interactively if only one file is processed.

Example:
    python plot_single.py config.yaml
""")


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("--help", "-h"):
        print_usage()
        return

    config_file = sys.argv[1]
    config = load_config(config_file)
    input_files = get_input_files(config)

    # determine if batch mode
    batch_mode = len(input_files) > 1

    for csv_file in input_files:
        print(f"Processing: {csv_file}")
        # Load CSV
        df = pd.read_csv(csv_file)
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
        plt.xlabel(config.get("axis_labels", {}).get("x", "Time [s]"), fontsize=fonts.get("axis", 14))
        plt.ylabel(config.get("axis_labels", {}).get("y", "Value"), fontsize=fonts.get("axis", 14))
        plt.title(config.get("plot_title", "CSV Plot"), fontsize=fonts.get("title", 16))
        plt.legend(fontsize=fonts.get("legend", 12))
        plt.tight_layout()
        plt.xlim(time_windowed[0], time_windowed[-1])
        plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)
        plt.xticks(fontsize=fonts.get("ticks", 12))
        plt.yticks(fontsize=fonts.get("ticks", 12))         
        # Save outputs
        filename = os.path.splitext(os.path.basename(csv_file))[0]
        output_dir = config.get("output_dir", "output")
        os.makedirs(output_dir, exist_ok=True)

        for fmt in config.get("save_formats", []):
            plt.savefig(f"{output_dir}/{filename}.{fmt}", format=fmt)

        if not batch_mode:
            plt.show()
        else:
            plt.close()

if __name__ == "__main__":
    main()
