# CSV PLOT COLLECTION
This repository will act as a central hub for different plot functions that should be reuseable for different purposes.
General setup is to separate the different plot script into subfolders that contain the `.py` script file and the `config.yaml`.
Currently there are the following scripts planned:
- single plot with single input file (first draft done)
  - add multi file support (automatically grab all .csv files in the `/input` folder - `[filename1, filename2]` or `[]` for all files in input folder)
- single plot with multiple input files to allow comparing data (expects the same csv format - time has to be matched)
- single plot with multiple input files to allow comparing data (from two different csv formats - time, sampling rate, etc has to be matched)
- mutlti subplots with single input file (2x1, 2x1 and 2x2 support)

This repository will be a work in progress.

# Requirements

Install dependencies with:
```
pip install pandas matplotlib pyyaml
```