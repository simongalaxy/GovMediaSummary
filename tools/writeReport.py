import os
from pathlib import Path
import textwrap
from datetime import datetime


def write_report(markdown: str) -> str:
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # generate filename by daily press release url.
    filename = f"Media_Summary_Report-{current_timestamp}.md"
    filepath = "./reports/"
    
    # generate report in text file.
    with open(os.path.join(filepath, filename), "w", encoding="utf-8") as file:
        file.write(markdown + "\n")
        
    return filename
        