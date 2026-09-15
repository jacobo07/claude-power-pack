Inject AKOS knowledge into any project before starting work.

Arguments: $ARGUMENTS

## What This Does
Queries the AKOS Knowledge Store (30,000+ canonical units from Skool courses, YouTube channels, MillionaireFlx, business datasets) and generates a curated knowledge brief for the current task or project.

## Commands

### Auto-inject into current project
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/TUAX_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" inject "<project_path>"
```

### Query by keywords
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/TUAX_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" query "$ARGUMENTS"
```

### Generate brief for specific domains
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/TUAX_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" brief --project "ProjectName" --domain "sales,marketing,ecommerce"
```

### List available domains
```
python "C:/Users/User/Desktop/Cursor Projects/TUA-X/TUAX_UGC_SYSTEM/tools/skool-scraper/knowledge_engine.py" domains
```

## Available Domains
seo, ecommerce, sales, outreach, marketing, social_media, scaling, wealth, mindset, ai_automation, copywriting, saas

## Usage
Based on $ARGUMENTS, run the appropriate command. If no arguments, auto-inject into the current working directory project.
Read the generated AKOS_KNOWLEDGE_BRIEF.md and use it to inform your work.
