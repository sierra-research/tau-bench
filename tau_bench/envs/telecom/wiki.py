
import os

# Read the wiki content from the markdown file
wiki_path = os.path.join(os.path.dirname(__file__), "wiki.md")
with open(wiki_path, "r") as f:
    WIKI = f.read()