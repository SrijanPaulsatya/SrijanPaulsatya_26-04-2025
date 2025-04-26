# Generate Report

### Getting Started:
- Run the fetch.sh for getting the csv data
- python3 -m venv .venv
- source .venv/bin/activate
- pip install requirements.txt
- fastapi dev app.py
- Sample report is in Reports directory



### Improvements:

1. Can Improve the readibility(for sure):
    - Nesting can be reduce
    - 2 many if blocks(I think I was in the Go lang zone)
2. Uptime/Downtime hours can be more reasonably guessed by seeing the general past trends for each day (current logic is little different)
