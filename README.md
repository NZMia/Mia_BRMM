
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=plastic)](https://github.com/prettier/prettier)  
[![code commit rule: commitlint](https://img.shields.io/badge/code_commite-commitlint-ff69b4.svg?style=plastic)](https://github.com/conventional-changelog/commitlint)

# Mia_BRMM
This web application is built for the BRMM Car Club to manage and display results for their monthly Motorkhana event. The application provides two distinct interfaces - one for public/driver access and another for club administrators. This README provides an overview of the project structure and key functionalities 

![development: DONE](https://img.shields.io/badge/development-DONE-informational.svg?style=plastic)


### Structure

---

- static
- templates
  - component (reusable components)
    - card.html (reusable card template)
  - layout
    - adminLayout.html (layout for admin routes' pages)
    - base.html (general layout for the entire application)
    - driverLayout.html (layout for driver routes' pages)
  - routes
    - admin
      - addDriver.html (Page for adding drivers)
      - driverSearch.html (Driver search page)
      - editRun.html (Page for editing runs)
      - juniorList.html (List of junior drivers)
      - runSearch.html (Run search page)
    - visitor (driver)
      - courseList.html (List of courses)
      - driverDetail.html (Driver details page)
      - driverList.html (List of all drivers)
      - driverListDropdown.html (Dropdown list of drivers)
      - overallResult.html (Overall results page)
      - top5graph.html (Horizontal bar graph of top 5 drivers)
  - admin.html (Admin dashboard entry point)
  - home.html (Home page for visitors/drivers)
- app.py (Main Flask application file)  

### Routes

---

| Route | HTTP Method | Description | Parameters |
|-------|-------------|-------------|------------|
| `/` | GET | Renders the home page. | None |
| `/courses` | GET | Lists all available courses. | None |
| `/drivers` | GET | Lists all drivers or provides a dropdown list of drivers. | `is_run_details` (query parameter) - Used to determine whether to display a dropdown list of drivers. |
| `/driver` | GET or POST | Displays details for a specific driver, including their runs. | - GET: `driver_id` (query parameter) - Specifies the driver's ID for displaying details. | - POST: `selected_driver` (form data) - Selects a driver for displaying details. |
| `/results` | GET | Displays overall results for drivers. | None |
| `/graph` | GET | Displays a horizontal bar graph of the top 5 drivers. | None |
| `/admin` | GET | Entry point for the admin dashboard. | None |
| `/junior_list` | GET | Lists junior drivers with or without caregivers. | None |
| `/driver_search` | GET or POST | Allows administrators to search for drivers. | - POST: `partial_text` (form data) - Search term to find drivers. |
| `/run_search` | GET or POST | Enables administrators to search for runs by driver or course. | - POST: `selected_driver` (form data) - Selects a driver for run search. | - POST: `selected_course` (form data) - Selects a course for run search. |
| `/edit_run` | GET or POST | Allows administrators to edit run details for a specific driver and course. | - GET: `driver_id`, `name`, `course_id`, `run_num`, `seconds`, `cones`, `wd` (query parameters) - Details of the run to edit. | - POST: Form fields for editing run details (e.g., `seconds`, `cones`, `wd`). |
| `/add_driver` | GET or POST | Provides a form for adding new drivers with various validation checks. | - GET: None | - POST: Form fields for adding a new driver (e.g., `first_name`, `surname`, `car`, `date_of_birth`, `caregiver`). |

### Assumptions and Design Decisions

---

#### Choice of Technology Stack  

- Flask and Python  

### Usage

---

To run the application:

1. Clone this repository.
2. Install the necessary dependencies with `pip install -r requirements.txt`.
3. Set up the MySQL database and update the database configuration in `connect.py`.
4. Run `python app.py` to start the Flask application.


### Contributors

- [Mia](https://github.com/NZMia) - Project Developer

## License

This project is licensed under the [MIT License](LICENSE).



### Installation

Installation is handled via [pip](https://pip.pypa.io/en/stable/cli/pip_install/)

To create a new project based on this repo, run:

---

### Running
```shell
pip -m flask
```
---

#### Local env

Python 3.9.6 
pip 23.2.1

#### Technology

Python  
Flask  
MySQL  

Bootstrap
