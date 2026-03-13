# Granola Local Exporter

## ⚠️ Project Status: Broken / Unmaintained

> **This project is currently broken** due to upstream changes in Granola and is **no longer actively maintained**.
>
> The exporter relied on Granola's local cache format, which has since changed. Until those changes are addressed, this tool will not function as expected. No known workaround exists at this time.
>
> **What you can do:**
> - Fork this repository and adapt it to Granola's updated behavior.
> - Watch the repository for any future updates.
>
> Support requests and bug reports are unlikely to be addressed. Use this project at your own risk.

---

A powerful tool to export your meeting data from Granola.ai into well-structured Markdown files. This tool accesses your local Granola cache directly, ensuring specific formatted extraction of your Enhanced Notes, Summaries, and Transcripts.

Perfect for integrating Granola notes with PKM systems like Obsidian, Notion, or any markdown-based workflow.

## Features

- **Enhanced Notes Extraction** - Pulls the AI-generated summaries, action items, and key takeaways
- **Markdown Formatting** - Preserves **bold**, *italics*, lists, headings, and links
- **Folder Support** - Automatically moves exported notes into folders (e.g., "Customer Meetings", "1on1s") matching your Granola setup
- **Date Filtering** - Perfect for daily automation (e.g., "Export only yesterday's notes")
- **Auto-Cleanup** - Automatically organizes your export folder, removing duplicates if a file moves into a subfolder
- **Timestamps (Optional)** - Include relative timestamps and audio source labels in transcripts for AI analysis

---

## Installation

### Prerequisites
- Python 3.6 or higher
- macOS (Granola is macOS-only)
- Active Granola.ai installation

### Install

1.  Clone this repository:
    ```bash
    git clone https://github.com/phanclan/granola-exporter.git
    cd granola-exporter
    ```

2.  Make the helper script executable:
    ```bash
    chmod +x run_export.sh
    ```

3.  Test the installation:
    ```bash
    ./run_export.sh --help
    ```

---

## Usage

### 1. One-Click Export (Everything)

```bash
./run_export.sh
```

### 2. Daily Automation (Last 24 Hours)
Run this command to export only notes from the **last 24 hours** and organize them into folders.

```bash
./run_export.sh --days 1 --folders
```

### 3. Catch-Up Export
Export notes from the **last 30 days**.

```bash
./run_export.sh --days 30 --folders
```

### 4. Custom Output Directory
Export to a specific location.

```bash
./run_export.sh --output-dir ~/Obsidian/Meetings --folders
```

### 5. With Timestamps (AI Analysis)
Include timestamps and audio source labels in transcripts. Useful for feeding to AI tools or referencing specific moments.

```bash
./run_export.sh --days 1 --folders --timestamps
```

**Example output:**
```
[0:00] **System Audio**: Our numbers are still climbing up...
[0:10] **System Audio**: But I will share. We do have SKO...
[2:39] **Microphone**: Thanks for sharing that...
```

---

## Command-Line Options

All flags can be combined as needed.

| Flag | Description | Example |
|------|-------------|---------|
| `--days N` | Export notes from the last N days | `--days 7` |
| `--start-date YYYY-MM-DD` | Export notes on or after this date | `--start-date 2026-01-01` |
| `--folders` | Organize exports into subfolders based on Granola lists | `--folders` |
| `--timestamps` | Include timestamps and audio source in transcripts (for AI) | `--timestamps` |
| `--output-dir PATH` | Custom output directory (default: sibling `Granola-Export/` folder) | `--output-dir ~/Notes` |
| `--help` | Show help message with all options | `--help` |

**Examples:**
```bash
# Export last week with folder organization
./run_export.sh --days 7 --folders

# Export to custom location with timestamps
./run_export.sh --output-dir ~/Obsidian/Meetings --timestamps --folders

# Export everything from January onwards
./run_export.sh --start-date 2026-01-01 --folders
```

---

## Automation (Cron Job)

You can schedule this script to run automatically every morning using `cron`.

1.  Open your crontab editor:
    ```bash
    crontab -e
    ```
2.  Add the following line to run at **8:00 AM every day**:
    *(Replace `/path/to/granola-exporter` with the actual path to this folder)*

    ```bash
    0 8 * * * /path/to/granola-exporter/run_export.sh --days 1 --folders >> ~/Library/Logs/granola_export.log 2>&1
    ```

---

## Configuration

### Output Directory
By default, files are saved to `Granola-Export` folder (sibling to the `granola-exporter` folder).

**To change the output location:**
- Use the `--output-dir` flag:
  ```bash
  ./run_export.sh --output-dir ~/Obsidian/Meetings
  ```
- Or edit the `DEFAULT_EXPORT_DIR` variable in `granola_exporter.py`

### Folder Mapping
The script automatically reads your Granola "Lists" metadata to map documents to folders.
- Use the `--folders` flag to enable this.
- If a note belongs to a list (e.g., "Customer Meetings"), it will be placed in a corresponding subfolder.

---

## Troubleshooting

### Duplicate files in root and folder
The script has a built-in cleanup mechanism. Run the export **with** the `--folders` flag again. It will detect if a file has moved to a subfolder and delete the old root copy.

```bash
./run_export.sh --folders
```

### Debugging Schema
If Granola updates their app and the script stops working, a debug tool is included:
```bash
python3 inspect_schema.py
```

---

## Contributing

Found a bug or have a feature request? Contributions are welcome!

1. **Report Issues**: Open an issue on GitHub with details about the problem
2. **Submit Pull Requests**: Fork the repo, make your changes, and submit a PR
3. **Share Feedback**: Let us know how you're using this tool

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Credits

Created by [Peter Phan](https://github.com/phanclan)

If this tool saves you time, consider:
- Starring the repository
- Reporting bugs or suggesting features
- Sharing with others who use Granola

---

## Disclaimer

This tool is not affiliated with or endorsed by Granola.ai. It accesses your local Granola cache file for personal use only. Use at your own discretion.
