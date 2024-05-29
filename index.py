from flask import *
from flask_login import login_required
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

ADMIN_CREDENTIALS = {
    'admin': 'password123'
}

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "KrrrzPPghtfgSKbtJEQCTA"
JSON_FILE_PATH = "registrations.json"

from functools import wraps

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = file.read()
            if data.strip():  # Check if the file is not empty
                return json.loads(data)
            else:
                print("JSON file is empty.")
                return {}
    except FileNotFoundError:
        print("File not found.")
        return {}
    except json.decoder.JSONDecodeError as e:
        print("JSON decoding error:", e)
        return {}
    except Exception as e:
        print("Error:", e)
        return {}

def profile_exists(username):
    """Check if the profile exists in the JSON file."""
    data = load_json_file(JSON_FILE_PATH)
    return username in data

@app.route('/admin_login.html')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin_authenticate', methods=['POST'])
def admin_authenticate():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            return redirect(url_for('data_table'))
        else:
            return render_template('admin_login.html', error='Invalid username or password')

@app.route('/data_table')
def data_table():
    data = load_json_file(JSON_FILE_PATH)
    if data:
        return render_template('data_table.html', data=data)
    else:
        return "No data available."

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            session.get("roll")
            return func(*args, **kwargs)
        except Exception as e:
            return str(e)
    return decorated_view

def profiler(username, pwd):
    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text, "html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:

        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/AttWfStudProfile.aspx'
    
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text,"html.parser")

        image_url = "https://ecampus.psgtech.ac.in/studzone2/WfAttStudPhoto.aspx"
        response = session.get(image_url)

        # Return the image data as a response
        image_data = response.content

        data = []
        column = []
    
        try:

            table = soup.find('table', attrs={'id':'ItStud'})

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele]) # Get rid of empty val

            table = soup.find('table', attrs={'id':'DlsAddr'})
            addr = []

            rows = table.find_all('tr')
            for index,row in enumerate(rows):
                
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                addr.append([ele for ele in cols if ele]) # Get rid of empty val

            return {"student":data, "address":addr, "image":image_data}

        except Exception as e:
            
            return str(e)
    else:
        return item_request_body

def test_timetable(req_info):
    username = req_info.get("roll")
    pwd = req_info.get("pass")

    session = requests.Session()
    r = session.get('https://ecampus.psgtech.ac.in/studzone2/')
    loginpage = session.get(r.url)
    soup = BeautifulSoup(loginpage.text, "html.parser")

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
    viewstategen = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

    item_request_body = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__EVENTVALIDATION': eventvalidation,
        'rdolst': 'S',
        'txtusercheck': username,
        'txtpwdcheck': pwd,
        'abcd3': 'Login',
    }

    response = session.post(url=r.url, data=item_request_body, headers={"Referer": r.url})
    val = response.url

    if response.status_code == 200:
        defaultpage = 'https://ecampus.psgtech.ac.in/studzone2/FrmEpsTestTimetable.aspx'
        page = session.get(defaultpage)
        soup = BeautifulSoup(page.text, "html.parser")

        data = []
        slots = []

        try:
            table = soup.find('table', attrs={'id': 'DgResult'})
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele])  # Get rid of empty val

            table = soup.find_all('table', attrs={'width': '85%', 'align': 'center'})[-1]
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                slots.append([ele for ele in cols if ele])  # Get rid of empty val

            return {"slots": slots, "timetable": data}

        except Exception as e:
            return "Invalid password"
    else:
        return item_request_body

@app.route('/')
def slash():
    if session.get("roll"):
        return redirect(url_for("final_login"))
    else:
        session.clear()
        return redirect(url_for("authenticate"))

@app.route('/auth', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'GET':
        return render_template('signup.html', err=False)
    else:
        username = request.form.get("userid").upper()
        password = request.form.get("pwd")
        
        # Check if the profile exists in the JSON file
        if profile_exists(username):
            return render_template("signup.html", err=True, message="Profile already exists.")
        
        # Proceed with profiling and authentication
        profile = profiler(username, password)
        
        try:
            session["name"] = (str(profile["student"][0][2])).title()
            session["login"] = "done"
            session["roll"] = username
            session["pwd"] = password
            session["programme"] = profile["student"][1][2]
            session["semester"] = profile["student"][1][3]  # Assuming semester is stored at index 3
            
            # Update department and year based on profile data
            session["department"] = profile["student"][1][2]  # Assuming department is stored at index 2
            print("Department:", session["department"])  # Debug statement
            session["year"] = sem_to_year(session["semester"])  # Convert semester to year
            print("Year:", session["year"])  # Debug statement
            
            try:
                tests = test_timetable({"roll": username, "pass": password})
                time_table = []
                for i in tests["timetable"][1:]:
                    time_table.append({
                        "sem": i[0],
                        "course": i[1],
                        "title": " ".join([j.capitalize() for j in i[2].split(" ")]),
                        "date": f"{i[3]}",
                        "slot": f"{i[4]}"
                    })
                session["semester"] = time_table[0].get("sem")
                session["phone"] = str(profile.get("address")[0][-1]).split("Student Mobile:")[-1].split(" ")[0].strip()
            except:
                pass
            
            return redirect(url_for("final_login"))
        
        except Exception as e:
            session.clear()
            return render_template("signup.html", err=True, message="Failed to authenticate.")
        
@app.route('/clear')
def clear_sesh():
    session.clear()
    return redirect(url_for("slash"))

def sem_to_year(semester):
    """Convert semester to corresponding year."""
    sem_to_year_dict = {
        "1": "1st",
        "2": "1st",
        "3": "2nd",
        "4": "2nd",
        "5": "3rd",
        "6": "3rd",
        "7": "4th",
        "8": "4th"
    }
    return sem_to_year_dict.get(str(semester), "Unknown")

@app.route('/final_login', methods=['GET', 'POST'])
@login_required
def final_login():
    sem_to_year_dict = {
        "1": "1st",
        "2": "1st",
        "3": "2nd",
        "4": "2nd",
        "5": "3rd",
        "6": "3rd",
        "7": "4th",
        "8": "4th"
    }
    name = session["name"].replace(" ", "+")
    if "BE COMPUTER SCIENCE & ENGINEERING" in session['programme']:
        if "ARTIFICIAL INTELLIGENCE" in session['programme']:
            dept = "CSE+(AI+%26+ML)"
        else:
            dept = "CSE"
        session["year"] = sem_to_year(str(session["semester"]))  # Convert semester to year
        return render_template('profile.html', name=session["name"], roll=session["roll"],
                               department=session["programme"], year=session["year"],
                               phone=session["phone"], options=["Web Development", "Cybersecurity", "Artificial Intelligence"])
    return "This is only for CSE Students."

@app.route('/submit_option', methods=['POST'])
def submit_option():
    if request.method == 'POST':
        try:
            # Check if the request contains JSON data
            if request.is_json:
                data = request.json
                selected_option = data.get('selected_option')
                roll_number = session.get('roll')
                name = session.get('name')
                department = session.get('department')
                year = session.get('year')
                phone_number = session.get('phone')

                # If roll number is already registered, show an error message
                registrations = load_json_file(JSON_FILE_PATH)
                if roll_number in registrations:
                    return "You have already submitted your option."

                # Add the new registration data
                registrations[roll_number] = {
                    'name': name,
                    'department': department,
                    'year': year,
                    'phone': phone_number,
                    'selected_option': selected_option
                }

                # Write the updated registrations to the JSON file
                with open(JSON_FILE_PATH, 'w') as file:
                    json.dump(registrations, file, indent=4)

                # Redirect to a success message page
                return redirect(url_for('success_message'))

            else:
                return "Error: Invalid JSON data received."

        except json.JSONDecodeError as e:
            # Log the JSON decoding error
            print("JSON Decoding Error:", e)
            return "Error: Invalid JSON data received."

        except Exception as e:
            return "Error: " + str(e)

    else:
        return "Error: Invalid request method."

@app.route('/success_message.html')
def success_message():
    return render_template('success_message.html')

def load_registrations():
    try:
        with open(JSON_FILE_PATH, "r") as file:
            data = file.read()
            if data.strip():  # Check if the file is not empty
                return json.loads(data)
            else:
                return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        return []
    
def main():
    app.run(host='0.0.0.0', port=5500, debug=True)

if __name__ == '__main__':
    app.run(debug=True) 
