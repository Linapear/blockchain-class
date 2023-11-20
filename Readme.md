# Activate Virtual Environment (Optional but Recommended):
It's a good practice to create and activate a virtual environment for your project before installing any packages. This helps isolate your project's dependencies from the global Python environment.
```
# Create a virtual environment (Python 3)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate   # On Linux or macOS
```

# Generate requirements.txt:
Once you have installed all the required packages, you can generate a requirements.txt file that lists all the installed packages and their versions.
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
flask --app node_server run -h 127.0.0.1 -p 8080
```