
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=plastic)](https://github.com/prettier/prettier)  
[![code commit rule: commitlint](https://img.shields.io/badge/code_commite-commitlint-ff69b4.svg?style=plastic)](https://github.com/conventional-changelog/commitlint)

# Mia_BRMM
This web application is built for the BRMM Car Club to manage and display results for their monthly Motorkhana event. The application provides two distinct interfaces - one for public/driver access and another for club administrators. This README provides an overview of the project structure and key functionalities 

![development: DONE](https://img.shields.io/badge/development-DONE-informational.svg?style=plastic)


## Structure  

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
      - driverDetail.html (Driver's run details page)
      - driverList.html (List of all drivers)
      - driverListDropdown.html (Dropdown list of drivers)
      - overallResult.html (Overall results page)
      - top5graph.html (Horizontal bar graph of top 5 drivers)
  - admin.html (Admin dashboard entry point)
  - home.html (Home page for visitors/drivers)
- app.py (Main Flask application file)  

## Routes

---

| Route | HTTP Method | Description | Template | Parameters |
|-------|-------------|-------------|------------|------------|
| `/` | GET | Renders the home page. | home.html | None |
| `/courses` | GET | Lists all available courses. | routes/visitor/courseList.html | None |
| `/drivers` | GET | Lists all drivers. | routes/visitor/driverList.html | `is_run_details` (query parameter) - Used to determine whether to display a dropdown list of drivers. |
| `/drivers?is_run_details=dropdown` | GET | Provides a dropdown list of drivers. | routes/visitor/driverListDropdown.html | `is_run_details` (query parameter) - Used to determine whether to display a dropdown list of drivers. |
| `/driver` | GET | Displays details for a specific driver, including their runs. |  routes/visitor/driverDetail.html |- GET: `driver_id` (query parameter) - Specifies the driver's ID for displaying details. | 
| `/driver` | POST | Displays details for a specific driver, including their runs. |  routes/visitor/driverDetail.html | - POST: `selected_driver` (form data) - Selects a driver for displaying details. |
| `/overall_results` | GET | Displays overall results for drivers. |routes/visitor/overallResult.html | None |
| `/graph` | GET | Displays a horizontal bar graph of the top 5 drivers. | routes/visitor/top5graph.html | None |
| `/admin` | GET | Entry point for the admin dashboard. | admin.html | None |
| `/junior_list` | GET | Lists junior drivers with or without caregivers. | routes/admin/juniorList.html |None |
| `/driver_search` | GET | Allows administrators to search for drivers. | routes/admin/driverSearch.html | None |
| `/driver_search` | POST | Allows administrators to search for drivers. | routes/admin/driverSearch.html | - POST: `partial_text` (form data) - Search term to find drivers. |
| `/run_search` | GET | Enables administrators to search for runs by driver or course. |routes/admin/runSearch.html | None |
| `/run_search` | POST | Enables administrators to search for runs by driver or course. | routes/admin/runSearch.html |- POST: `selected_driver` (form user select) - Selects a driver for run search. |
| `/run_search` | POST | Enables administrators to search for runs by driver or course. | routes/admin/runSearch.html | - POST: `selected_course` (form user select) - Selects a course for run search. |
| `/edit_run` | GET | Allows administrators to edit run details for a specific driver and course. | routes/admin/editRun.html | - GET: `driver_id`, `name`, `course_id`, `run_num`, `seconds`, `cones`, `wd` (query parameters) - Details of the run to edit. | 
| `/edit_run` | POST | Allows administrators to edit run details for a specific driver and course. | routes/admin/editRun.html | - POST: Form fields for editing run details (`seconds`, `cones`, `wd`). |
| `/add_driver` | GET  | Provides a form for adding new drivers with various validation checks. | routes/admin/addDriver.html | None |
| `/add_driver` | POST | Provides a form for adding new drivers with various validation checks. | routes/admin/addDriver.html | - POST: Form fields for adding a new driver (e.g., `first_name`, `surname`, `car`, `date_of_birth`, `caregiver`). |  

## Assumptions and Design Decisions

---

#### Choice of Technology Stack  

- **Flask and Python**：
    - We have opted for Flask and Python as the primary development framework and programming language for this project. This decision is based on several factors, including their lightweight nature, ease of learning, and extensive community support. Flask provides us with flexibility, allowing us to focus on solving business problems without being constrained by overly complex framework structures.
- **Database Selection - MySQL**
    - We have decided to use MySQL as the database management system. This choice is influenced by its widespread use in the realm of relational databases, its outstanding stability, and its robust scalability. The decision is further influenced by the structured nature of our data and our data management needs.
- **Frontend Selection - HTML with Bootstrap**
    - We have adopted HTML and Bootstrap as the frontend technology stack. Bootstrap's design philosophy and component library provide substantial convenience for user interface design and development. This choice enables us to focus more effectively on implementing business logic without expending excessive effort on interface construction.

#### Code Reusability
- **Component Reusability Strategy**
    - Certain components and functionalities in the project require reuse across different sections. To minimise code redundancy and enhance maintainability, we have opted to extract these components into independent modules. This strategy ensures cleaner and more reusable code.
        - card.html
        - layout/
        - routes/visitor/driverDetail.html (see above Route)


- **Router Reusability Strategy**
    - When dealing with multiple similar requests that render the same page, consider combining routers and using variables to control router parameters. For example, refer to the paths `/drivers` and `/drivers?is_run_details=dropdown.` In such cases, we can utilise GET/POST requests to obtain the relevant parameters. This approach enhances code reusability and maintains consistency in rendering pages with similar content.
      
#### User Privacy
- **Role-Based Functionality Presentation**
    - In this project, user privacy and role-based distinctions are crucial for data security. For instance, specific functionalities, such as those intended for administrators (admin), require user login verification. While this design does not include actual login authentication, we have devised specific event triggers to simulate administrator privileges, ensuring data security.

#### Scalability
- **Addition and Maintenance of New Features**  
    - We have placed a strong emphasis on designing the project to facilitate the easy addition of new features, such as login and registration. This design decision allows us to extend functionality based on the diverse requirements of user roles and simplifies the addition and maintenance of new features. Such a design ensures long-term maintainability and flexibility for the project.

#### Error Handling:
- **Proper Error Messaging**
  - From a user experience perspective, we should not restrict user input. However, we can guide users by setting appropriate error messages, limiting their progress to the next step, and displaying error messages to them.

#### Clear Project Structure:
  - A clear and well-structured directory layout is essential for making the iterative development process more manageable. (see above Structure)

## Usage

---

To run the application:

1. Clone this repository.
2. Install the necessary dependencies with `pip install -r requirements.txt`.
3. Set up the MySQL database and update the database configuration in `connect.py`.
4. Run `python app.py` to start the Flask application.

## Database 

---

  - **What SQL statement creates the car table and defines its three fields/columns?**
    ```sql
      CREATE TABLE IF NOT EXISTS car(
        car_num INT PRIMARY KEY NOT NULL,
        model VARCHAR(20) NOT NULL,
        drive_class VARCHAR(3) NOT NULL
      );
    ```
  - **Which line of SQL code sets up the relationship between the car and driver tables?**
    ```sql
      FOREIGN KEY (car) REFERENCES car(car_num)
      ON UPDATE CASCADE
      ON DELETE CASCADE
    ```
  - **Which 3 lines of SQL code insert the Mini and GR Yaris details into the car table?**
    ```sql
      INSERT INTO car VALUES
        (11,'Mini','FWD'),
        (17,'GR Yaris','4WD'),
    ```
  - **Suppose the club wanted to set a default value of ‘RWD’ for the driver_class field.  What specific change would you need to make to the SQL to do this?**
    ```sql
      CREATE TABLE IF NOT EXISTS car (
        car_num INT PRIMARY KEY NOT NULL,
        model VARCHAR(20) NOT NULL,
        drive_class VARCHAR(3) DEFAULT 'RWD' NOT NULL
      );
    ```
  - **Suppose logins were implemented.  Why is it important for drivers and the club admin to access different routes?**
    - Data Privacy:
      - Different user roles often require access to distinct sets of data. For example, drivers may only need to access their personal performance data and courses and not be allowed to update others' data. In contrast, administrators might need access to all club-related information and update other's data as required. Allowing everyone to access the same routes could lead to unauthorised user access to sensitive data and modification, compromising data privacy.
        
    - Functionality Restrictions:
      - Different roles may have specific functionalities they need to perform. For instance, administrators can add a new driver, but this functionality should not be available to visitors. Additionally, only administrators can edit results. If both user roles have access to all functionalities, it can lead to misuse or unintended actions. For example, a driver might mistakenly modify another driver's data. This underscores the significance of restricting access to functionalities based on user roles to prevent inadvertent actions and ensure the proper execution of tasks.

## Contributors  

---

- [Mia](https://github.com/NZMia) - Project Developer

## License  

---

This project is licensed under the [MIT License](LICENSE).


## Local env

Python 3.9.6   
pip 23.2.1  


## Technology

Python  
Flask  
MySQL  
Bootstrap
