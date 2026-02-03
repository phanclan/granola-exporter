
import os
import json
import datetime
import re
import argparse

# Configuration
GRANOLA_CACHE_PATH = os.path.expanduser("~/Library/Application Support/Granola/cache-v3.json")

# Default export directory: sibling folder to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXPORT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "Granola-Export")

def clean_filename(s):
    """Sanitize string for filename."""
    s = s.replace("|", "-").replace(":", "-").replace("/", "-")
    return re.sub(r'[\\/*?:"<>|]', "", s).strip()

def extract_text_from_prosemirror(node):
    """Recursively extract text from ProseMirror JSON structure to Markdown."""
    if not isinstance(node, dict):
        return ""
    
    node_type = node.get("type")
    content = node.get("content", [])
    text = ""

    # handle leaf text node
    if node_type == "text":
        text = node.get("text", "")
        # Apply marks if present
        marks = node.get("marks", [])
        for mark in marks:
            m_type = mark.get("type")
            if m_type == "bold" or m_type == "strong":
                text = f"**{text}**"
            elif m_type == "italic" or m_type == "em":
                text = f"_{text}_"
            elif m_type == "code":
                text = f"`{text}`"
            elif m_type == "link":
                href = mark.get("attrs", {}).get("href", "")
                text = f"[{text}]({href})"
        return text

    # Recursive step for container nodes
    inner_text = ""
    for child in content:
        inner_text += extract_text_from_prosemirror(child)

    # Apply formatting based on node type
    if node_type == "paragraph":
        return f"{inner_text}\n\n"
    
    elif node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        return f"{'#' * level} {inner_text}\n\n"
    
    elif node_type == "bulletList":
        return f"{inner_text}\n"
    
    elif node_type == "orderedList":
        # Note: We aren't tracking index here for simplicity, typically PM handles this via separate logic or CSS 
        # but for MD export we can just assume 1. for all and let MD renderer handle it or try to track.
        # However, for valid MD, "1." repeatedly works. 
        # But wait, children of orderedList are listItems. We need to pass context or handle in listItem.
        # A simple hack is to rely on listItem to prepend. But listItem doesn't know parent.
        # Let's handle it by treating inner_text differently? No, simpler to just return inner
        # AND we might need to handle indentation for nested lists (todo for complex cases)
        return f"{inner_text}\n"

    elif node_type == "listItem":
        # This is a bit tricky because we don't know if parent is ordered or bullet.
        # Heuristic: Default to bullet "- " unless we can pass context. 
        # Given this is a recursive function without context, strict ordered lists are hard.
        # However, for meeting notes, bullets are 99% of cases.
        # To fix correctly, we'd need to change signature to accept context or refactor.
        # For now, let's use "- ". PROPOSE: Just use "- " for everything.
        # Also need to handle multi-paragraph list items.
        # Removing trailing newlines from inner_text to avoid huge gaps
        clean_inner = inner_text.strip()
        # Indent subsequent lines if multiple paragraphs?
        # For MVP: just prefix first line.
        return f"- {clean_inner}\n"

    elif node_type == "hardBreak":
        return "  \n"

    elif node_type == "doc":
        return inner_text

    else:
        # Default fallthrough for unknown containers
        return inner_text

def parse_args():
    parser = argparse.ArgumentParser(description="Export Granola meeting notes to Markdown.")
    parser.add_argument("--days", type=int, help="Export notes from the last N days.")
    parser.add_argument("--start-date", type=str, help="Export notes on or after this date (YYYY-MM-DD).")
    parser.add_argument("--folders", action="store_true", help="Organize exports into subfolders based on Granola lists/folders.")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_EXPORT_DIR,
                        help=f"Output directory for exported notes (default: {DEFAULT_EXPORT_DIR})")
    return parser.parse_args()

def main():
    args = parse_args()
    EXPORT_DIR = os.path.expanduser(args.output_dir)

    print(f"Reading Granola cache from: {GRANOLA_CACHE_PATH}")
    print(f"Export directory: {EXPORT_DIR}")

    # Date Filtering Setup
    cutoff_date = None
    if args.days:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=args.days)
        print(f"Filter: Exporting notes from the last {args.days} days.")
    if args.start_date:
        try:
            sd = datetime.datetime.fromisoformat(args.start_date)
            if cutoff_date and sd > cutoff_date:
                cutoff_date = sd
            elif not cutoff_date:
                cutoff_date = sd
            print(f"Filter: Exporting notes on or after {args.start_date}.")
        except ValueError:
            print("Error: Invalid start date format. Use YYYY-MM-DD.")
            return

    if not os.path.exists(GRANOLA_CACHE_PATH):
        print("Error: Cache file not found.")
        return

    try:
        with open(GRANOLA_CACHE_PATH, 'r') as f:
            raw_data = json.load(f)
            
        if 'cache' not in raw_data:
            print("Error: 'cache' key not found in JSON.")
            return
            
        inner_data = json.loads(raw_data['cache'])
        state = inner_data.get('state', {})
        documents = state.get('documents', {})
        transcripts = state.get('transcripts', {})
        panels = state.get('documentPanels', {})
        
        # Folder Mapping Logic
        folder_map = {} # doc_id -> folder_name
        if args.folders:
            # 1. Get List Names from Metadata
            list_names = {} # list_id -> name
            lists_meta = state.get('documentListsMetadata', {})
            for lid, l in lists_meta.items():
                list_names[lid] = clean_filename(l.get('title', 'Uncategorized'))
            
            # 2. Map Docs to Lists
            doc_lists = state.get('documentLists', {})
            for lid, doc_ids in doc_lists.items():
                folder_name = list_names.get(lid, "Unknown List")
                if isinstance(doc_ids, list):
                    for did in doc_ids:
                        folder_map[did] = folder_name
            
            print(f"Folder support enabled. Mapped {len(folder_map)} documents to folders.")
        
        print(f"Found {len(documents)} documents, {len(transcripts)} transcripts, and {len(panels)} panel entries.")

        if not os.path.exists(EXPORT_DIR):
            os.makedirs(EXPORT_DIR)
            print(f"Created export directory: {EXPORT_DIR}")

        documents_processed = 0
        files_created = 0
        skipped_count = 0
        
        for doc_id, doc in documents.items():
            try:
                if not isinstance(doc, dict):
                    continue
                    
                # 1. Metadata extraction
                title = doc.get('title', 'Untitled Meeting')
                created_at_str = doc.get('created_at')
                
                # Parse date for folder name and filtering
                date_prefix = "Unknown_Date"
                doc_date = None
                if created_at_str:
                    try:
                        # Handle ISO format variants
                        doc_date = datetime.datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        # Remove timezone info for simple comparison if cutoff is naive (usually easiest to make both aware or naive)
                        # simpler to make doc_date naive local or utc.
                        # Let's keep offset aware.
                        date_prefix = doc_date.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
                
                # Date Filter Check
                if cutoff_date and doc_date:
                    # Ensure cutoff is offset-aware if doc_date is
                    if doc_date.tzinfo and not cutoff_date.tzinfo:
                        cutoff_date = cutoff_date.replace(tzinfo=datetime.timezone.utc)
                    
                    if doc_date < cutoff_date:
                        skipped_count += 1
                        continue
                
                # Folder Name logic
                folder_name = clean_filename(f"{date_prefix} - {title}")
                
                # Determine Parent Folder
                parent_dir = EXPORT_DIR
                if args.folders:
                    sub_folder = folder_map.get(doc_id)
                    if sub_folder:
                        parent_dir = os.path.join(EXPORT_DIR, sub_folder)
                        if not os.path.exists(parent_dir):
                            os.makedirs(parent_dir)
                
                meeting_dir = os.path.join(parent_dir, folder_name)
                
                if not os.path.exists(meeting_dir):
                    os.makedirs(meeting_dir)
                
                # CLEANUP: Check if this meeting exists in the root and remove it to prevent duplicates
                # This handles the case where a previous run put it in root, but now it's in a folder.
                if args.folders and sub_folder:
                     root_meeting_path = os.path.join(EXPORT_DIR, folder_name)
                     if os.path.exists(root_meeting_path) and root_meeting_path != meeting_dir:
                         try:
                             # We can either delete it or move it. 
                             # Since we are about to overwrite/create the new one in the right place, 
                             # valid strategy is to remove the old one.
                             import shutil
                             shutil.rmtree(root_meeting_path)
                             print(f"Moved/Cleaned up old location: {folder_name}")
                         except Exception as e:
                             print(f"Warning: Could not remove old duplicate at {root_meeting_path}: {e}")
                    
                # 2. Extract Content
                # Prefer pre-rendered markdown if available
                notes_text = doc.get('notes_markdown') or ""
                if not notes_text:
                    notes_json = doc.get('notes', {})
                    if notes_json:
                        notes_text = extract_text_from_prosemirror(notes_json)
                
                # Extract AI Summary and Overview
                ai_summary = doc.get('summary') or ""
                ai_overview = doc.get('overview') or ""
                
                # 2.1 Extract Enhanced Panels (The missing piece)
                panels_text = ""
                doc_panels = panels.get(doc_id, {})
                if doc_panels:
                    # doc_panels is a dict of panel_id -> panel_obj
                    # We want to maybe sort them? or just append.
                    # Let's collect them.
                    collected_panels = []
                    for pid, panel in doc_panels.items():
                         if not isinstance(panel, dict):
                             continue
                         p_title = panel.get('title', 'Panel')
                         p_content = panel.get('content', {})
                         p_text = extract_text_from_prosemirror(p_content)
                         collected_panels.append(f"### {p_title}\n\n{p_text}\n")
                    
                    if collected_panels:
                        panels_text = "\n".join(collected_panels)

                summary_path = os.path.join(meeting_dir, "summary.md")
                with open(summary_path, 'w') as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"**Date:** {created_at_str}\n")
                    f.write(f"**ID:** {doc_id}\n\n")
                    
                    if panels_text:
                        f.write("## Enhanced Notes\n\n")
                        f.write(panels_text)
                        f.write("\n")

                    if ai_summary:
                        f.write("## AI Summary\n\n")
                        f.write(f"{ai_summary}\n\n")
                        
                    if ai_overview:
                        f.write("## Overview\n\n")
                        f.write(f"{ai_overview}\n\n")

                    f.write("## Original Notes\n\n")
                    f.write(notes_text)

                files_created += 1

                # 3. Extract Transcript
                transcript_segments = transcripts.get(doc_id)
                if transcript_segments:
                    with open(os.path.join(meeting_dir, "transcript.md"), 'w') as f:
                        f.write(f"# Transcript: {title}\n\n")
                        for segment in transcript_segments:
                            # Note: start_timestamp and source/speaker info available but not used
                            # for cleaner transcript formatting
                            text = segment.get('text', '')
                            f.write(f"{text}\n\n")
                    files_created += 1

                documents_processed += 1

            except Exception as e:
                print(f"Failed to process document {doc_id}: {e}")

        print(f"\nExport complete!")
        print(f"Documents processed: {documents_processed}")
        print(f"Files created: {files_created}")
        if skipped_count > 0:
            print(f"Documents skipped (date filter): {skipped_count}")
        print(f"Output location: {EXPORT_DIR}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
