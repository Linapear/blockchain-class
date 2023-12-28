# Activate Virtual Environment:
Create and activate a virtual environment for the project before installing any packages. This helps isolate the project's dependencies from the global Python environment.
```
# Create a virtual environment (Python 3)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate   # On Linux or macOS
```

# Generate requirements.txt:
After installed all the required packages, generate a requirements.txt file that lists all the installed packages and their versions.
```
pip freeze > requirements.txt
```

# Use requirements.txt for Dependency Installation:
To install the dependencies listed in the requirements.txt file on another machine or environment, use the following command:
```
pip install -r requirements.txt
```

# How to run server
```
source venv/bin/activate
flask --app node_server run -h 127.0.0.1 -p 8000 --debugger
```

# How to run app
```
source venv/bin/activate
python run_app.py
```
# How to push on github
```
git commit -m "Your commit message here"
git push origin main
```