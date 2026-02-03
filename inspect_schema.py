
import os
import json

granola_path = os.path.expanduser("~/Library/Application Support/Granola/cache-v3.json")

try:
    with open(granola_path, 'r') as f:
        data = json.load(f)
        
    state = json.loads(data['cache'])['state']
    
    lists = state.get('documentListsMetadata', {})
    print(f"Found {len(lists)} documentListsMetadata items.")
    
    # Print the "Customer Meetings" list to see structure
    for lid, l in lists.items():
        if l.get('title') == 'Customer Meetings':
            print(f"\n--- Customer Meetings (ID: {lid}) ---")
            print(json.dumps(l, indent=2))
            
    # Also check if there's a documentLists key?
    # Because 'Metadata' implies there might be a separate 'documentLists' key with the actual items
    dl = state.get('documentLists', {})
    if dl:
        print(f"\nFound {len(dl)} documentLists items.")
        # Print content of same ID if exists
        targets = [k for k,v in lists.items() if v.get('title') == 'Customer Meetings']
        if targets:
            tid = targets[0]
            if tid in dl:
                print(f"\n--- documentLists Content for {tid} ---")
                print(json.dumps(dl[tid], indent=2))

except Exception as e:
    print(f"Error: {e}")
