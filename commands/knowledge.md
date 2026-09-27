Inject AKOS knowledge into any project before starting work.

Arguments: $ARGUMENTS

## What This Does
Queries the AKOS Knowledge Store (30,000+ canonical units from Skool courses, YouTube channels, MillionaireFlx, business datasets) and generates a curated knowledge brief for the current task or project.

## Commands

### Auto-inject into current project
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/CW_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" inject "<project_path>"
```

### Query by keywords
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/CW_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" query "$ARGUMENTS"
```

### Generate brief for specific domains
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/CW_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" brief --project "ProjectName" --domain "sales,marketing,ecommerce"
```

### List available domains
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/CW_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" domains
```

## Available Domains
Run the `domains` command above -- it is the source of truth. A copied list here
went stale (the engine added community, gaming, monetization and v2v_video), and
the engine's path itself moved from `TUA-X/TUAX_UGC_SYSTEM` to `TUA-X/CW_UGC_SYSTEM`
without this file following, so every command below it failed for months.

## Usage
Based on $ARGUMENTS, run the appropriate command. If no arguments, auto-inject into the current working directory project.
Read the generated AKOS_KNOWLEDGE_BRIEF.md and use it to inform your work.
