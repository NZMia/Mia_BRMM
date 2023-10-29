from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from datetime import datetime

import mysql.connector
import connect

app = Flask(__name__)

dbconn = None
connection = None
is_redirect = False

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(
        user=connect.dbuser, 
        password=connect.dbpass, 
        host=connect.dbhost, 
        database=connect.dbname, 
        autocommit=True
    )
    dbconn = connection.cursor()
    return dbconn

def customer_sort(item):
    overall_result = item[1]['overall_results']

    if overall_result  == 'NQ':
        return (float('inf'), item[0])
    else:
        return (overall_result, item[0])
    
def getOverallResult():
    connection = getCursor()
    query = """
        WITH RankedData AS (
            SELECT 
                d.driver_id,
                CASE
                    WHEN d.age >= 12 AND d.age <= 25
                    THEN CONCAT(d.first_name, ' ', d.surname, '(J)')
                    ELSE  CONCAT(d.first_name, ' ', d.surname)
                END AS name,
                d.age,
                car.model, 
                car.car_num,
                c.course_id,
                c.name AS course_name,
                r.seconds + COALESCE(5 * r.cones, 0) + COALESCE(10 * r.wd, 0) 
                AS run_total,
                ROW_NUMBER() OVER (
                    PARTITION BY d.driver_id, c.course_id 
                    ORDER BY COALESCE(r.seconds, 99999)
                ) AS row_num

            FROM driver AS d
            JOIN run AS r ON d.driver_id = r.dr_id
            JOIN course AS c ON r.crs_id = c.course_id
            JOIN car AS car ON d.car = car.car_num
        )
        SELECT 
			driver_id,
			name,
			age,
			model,
			course_id,
			CASE
				WHEN COALESCE(run_total, 0) = 0 THEN 'dnf'
				ELSE FORMAT(run_total, 2)
			END AS course_time
		FROM RankedData AS t1
		WHERE row_num = 1;
    """
    connection.execute(query)
    original_data = connection.fetchall()
    calculate_overall_results = {}

    for item in original_data:
        driver_id, name, age, model, course_id, course_time = item
        # key = (driver_id, name, age, model)
        key = (driver_id, name, age, model)
        # value = course_time
        value = float(item[-1]) if item[-1] != 'dnf' else 0
    

        # calculate_overall_results: sum up the course_time for each driver
        # if the driver has not finished a course, the overall result will be 'NQ', 
        # otherwise, it will be the sum of course_time
        if key not in calculate_overall_results.keys():
            calculate_overall_results[key] = {
                'overall_results': value,
                course_id: course_time
            }
        else:
            # if the driver has not finished a course, the overall result will be 'NQ',
            # otherwise, it will be the sum of course_time
            if value != 0:
                calculate_overall_results[key]['overall_results'] = round(
                    calculate_overall_results[key]['overall_results'] + value, 
                    2
                )
            else:
                calculate_overall_results[key]['overall_results'] = 'NQ'
            
            # if the course has not been added to the driver's course list, add it
            if course_id not in calculate_overall_results[key]:
                calculate_overall_results[key][course_id] = course_time

    sorted_calculated_overall_result = sorted(calculate_overall_results.items(), key=customer_sort)

    return sorted_calculated_overall_result

def getDrivers(order_by_name=True):
    connection = getCursor()
    
    if order_by_name:
        query = """
            SELECT * 
            FROM driver, car 
            WHERE driver.car = car.car_num
            ORDER BY driver.surname, driver.first_name;
        """
    else:
        query = """
            SELECT * 
            FROM driver, car 
            WHERE driver.car = car.car_num;
        """
    
    connection.execute(query)
    driverList = connection.fetchall()
    return driverList


def calculate_age(date_of_birth):
    input_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
    current_date = datetime.now().date()

    current_age = current_date.year - input_date.year - ((current_date.month, current_date.day) < (input_date.month, input_date.day))

    return current_age

def add_driver_form_validation(current_age, has_not_caregiver, date_of_birth):
    error_message = []
    input_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
    current_date = datetime.now().date()

    if input_date > current_date:
        error_message.append('Date of birth cannot be in the future')
    if current_age < 12:
        error_message.append('Driver must be at least 12 years old')
    if current_age >= 12 and current_age <= 16 and has_not_caregiver :
        error_message.append('Drivers who are 16 or younger must also have a caregiver')

    return error_message

def add_driver_to_db(first_name, surname, date_of_birth, age, caregiver, car):
    connection = getCursor()
    try:
    # Create a new driver and add to database
        create_query = """
            INSERT INTO driver (first_name, surname, date_of_birth, age, car, caregiver)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        if len(date_of_birth) == 0:
            date_of_birth_format = None
            print('date of birth is null', date_of_birth)
        else:
            date_of_birth_format = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            print('date of birth is not null', date_of_birth)

        driver_date = (first_name, surname, date_of_birth_format, age, car, caregiver)
        connection.execute(create_query, driver_date)

        # Get the driver_id of the new driver
        driver_id = connection.lastrowid

        # Get the course_id from courses
        course_query = 'SELECT course_id FROM course;'
        connection.execute(course_query)
        course_list = connection.fetchall()

        # Create a run list
        run_list = [1, 2]

        # Create a run for each course for the new driver
        for course in course_list:
            for run in run_list:
                run_query = """
                    INSERT INTO run (dr_id, crs_id, run_num, seconds, cones, wd)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """
                run_data = (driver_id, course[0], run, None, None, 0)
                connection.execute(run_query, run_data)
    except Exception as e:
        raise e
    finally:
        connection.close()

    connection.close()


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

# ==================== Driver ====================

# Route: list all courses
@app.route('/courses', methods=['GET'])
def courses():
    connection = getCursor()
    query= 'SELECT * FROM course ORDER BY course.course_id;'
    connection.execute(query)
    course_list = connection.fetchall()
    return render_template('routes/visiter/courseList.html', course_list = course_list)

# Route: list all driver
@app.route('/drivers', methods=['GET'])
def drivers():
    is_run_details = request.args.get('is_run_details')
   
    if is_run_details:
        driver_list = getDrivers(order_by_name=False)
        return render_template(
            'routes/visiter/driversDropdown.html',
            driver_list = driver_list,
        )
    else:
        driver_list = getDrivers()
        return render_template(
            'routes/visiter/driverList.html',
            driver_list = driver_list
        )  

# Route: driver details
@app.route('/driver', methods=['GET', 'POST'])
def driver():
    connection = getCursor()
    driver_id = ''
    if request.method == 'POST':
        driver_id = request.form['selected_driver']
    else:
        driver_id = request.args.get('driver_id')

    driver_info = """
    SELECT d.driver_id, CONCAT(d.first_name, ' ', d.surname) as name,
    c.model, c.drive_class
    FROM driver AS d
        INNER JOIN car as c ON d.car = c.car_num
    WHERE d.driver_id = %s;
    """

    run_details = """
    SELECT co.name as course_name,
    r.run_num, r.seconds, r.cones, r.wd,
    FORMAT(
        r.seconds +
        COALESCE(5 * r.cones, 0) +
        COALESCE(10 * r.wd, 0),
        2
    ) as run_total
    FROM run AS r
        INNER JOIN course as co ON r.crs_id = co.course_id
    WHERE r.dr_id = %s;
    """
    connection.execute(driver_info, (driver_id,))
    driver_info = connection.fetchone()

    connection.execute(run_details, (driver_id,))
    run_details = connection.fetchall()

    return render_template('routes/visiter/driverDetails.html', driver = driver_info, runs = run_details)

# Route: Overall Results
@app.route('/overall_results', methods=['GET'])
def overall_results():
    sorted_data = getOverallResult()

    return render_template(
        'routes/visiter/overallResults.html', 
        rank_list = sorted_data
    )

# Route: Top 5 graph
@app.route('/graph')
def graph():
    original_data = getOverallResult()[:5]
    bestDriverList = []
    resultsList = []
   
    for item in original_data:
        driver = str(item[0][0]) + ' ' + str(item[0][1])
        result = item[1]['overall_results']
        bestDriverList.append(driver)
        resultsList.append(result)

    return render_template('routes/visiter/top5graph.html', name_list = bestDriverList, value_list = resultsList)

# ==================== Admin ====================
@app.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')

@app.route('/junior_list', methods=['GET'])
def junior_list():
    connection = getCursor()
    query = """
        SELECT d.*, IFNULL(CONCAT(c.first_name, ' ', c.surname), 'NO CAREGIVER ')  AS caregiver_name
        FROM driver AS d
            LEFT JOIN driver AS c ON d.caregiver = c.driver_id
        WHERE d.age BETWEEN 12 AND 25
        ORDER BY age desc, surname
        ;
    """
    connection.execute(query)

    junior_list = connection.fetchall()
    return render_template('routes/admin/juniorList.html', junior_list = junior_list) 

@app.route('/driver_search', methods=['GET', 'POST'])
def driver_search():
    driver_info = []
    show_results = False

    if request.method == 'POST':
        show_results = True 
        connection = getCursor()
        partial_text = request.form['partial_text']
        params = {'partial_text': '%' + partial_text + '%'}

        query = """
            SELECT *
            FROM driver as d
                WHERE d.first_name LIKE %(partial_text)s
                OR surname LIKE %(partial_text)s
            ;
        """
        connection.execute(query,  params)
        driver_info = connection.fetchall()
    
    return render_template('routes/admin/driverSearch.html', driver_info = driver_info, show_results = show_results)

@app.route('/run_search', methods=['GET', 'POST'])
def run_search():
    run_info = []
    show_results = False
    driver_id = ''
    course_id =''
    connection = getCursor()
    driver_info = """
        SELECT d.driver_id, concat(d.first_name, ' ', d.surname) as driver_name
        FROM driver as d;
    """
    course_info = """
        SELECT c.course_id, c.name as course_name
        FROM course as c;
    """
    connection.execute(driver_info)
    driver_run_info = connection.fetchall()

    connection.execute(course_info)
    course_details = connection.fetchall()

    if request.method == 'POST':
        if 'selected_driver' in request.form:
            driver_id = request.form['selected_driver']
        else:
            course_id = request.form['selected_course']

    if len(driver_id) > 0:
        driver_run_query = """
            SELECT  
                d.driver_id, 
                CONCAT(d.first_name, ' ', d.surname) AS driver_name, 
                r1.crs_id,
                c.name AS course_name,
                r1.run_num, r1.seconds, r1.cones, r1.wd
            FROM driver as d
                JOIN run AS r1 ON r1.dr_id = d.driver_id
                JOIN course AS c ON r1.crs_id = c.course_id
            WHERE d.driver_id = %s;
        """

        connection.execute(driver_run_query, (driver_id,))
        run_info = connection.fetchall()
        show_results = True
  
    if len(course_id) > 0:
        course_run_query = """ 
            SELECT  
                d.driver_id, 
                CONCAT(d.first_name, ' ', d.surname) AS driver_name, 
                r.crs_id,
                c.name AS course_name,
                r.run_num, r.seconds, r.cones, r.wd
            FROM course as c
                JOIN run as r on r.crs_id = c.course_id
                JOIN driver as d on d.driver_id = r.dr_id
            WHERE c.course_id = %s;
        """
        connection.execute(course_run_query, (course_id,))
        run_info = connection.fetchall()
        show_results = True
    
    return render_template(
        'routes/admin/runSearch.html',
        driver_run_info = driver_run_info,
        course_details = course_details,
        run_info = run_info, 
        show_results = show_results
    )

@app.route('/edit_run', methods=['GET', 'POST'])
def edit_run():
    connection = getCursor()
    is_redirect = False
    if request.method == 'POST':
        driver_id = request.form['driver_id']
        driver_name = request.form['driver_name']
        course_id = request.form['course_id']
        course_name = request.form['course_name']
        run_num = request.form['run_num']
        # name = request.form['name']

        if 'seconds' in request.form:
            seconds = request.form['seconds']
        if 'cones' in request.form:
            cones = request.form['cones']
        if 'wd' in request.form:
            wd = request.form['wd']

        query = """
            UPDATE run AS r
            JOIN driver AS d ON r.dr_id = d.driver_id
            SET r.seconds = %s, r.cones = %s, r.wd = %s
            WHERE d.driver_id = %s
            AND r.crs_id = %s
            AND r.run_num = %s;
        """
        connection.execute(query, (seconds, cones, wd, driver_id, course_id, run_num))
        is_redirect = True
        return render_template(
            'routes/admin/editRun.html', 
            driver_id = driver_id,
            driver_name = driver_name,
            course_id = course_id,
            course_name = course_name,
            run_num = run_num,
            seconds = seconds,
            cones = cones,
            wd = wd,
            is_redirect=is_redirect)
    else:
        is_redirect = False
        driver_id = request.args.get('driver_id')
        driver_name = request.args.get('driver_name')
        course_id = request.args.get('course_id')
        course_name = request.args.get('course_name')
        run_num = request.args.get('run_num')
        seconds = request.args.get('seconds')
        cones = request.args.get('cones')
        wd = request.args.get('wd')
        
        return render_template(
            'routes/admin/editRun.html', 
            driver_id = driver_id, 
            driver_name = driver_name, 
            course_id = course_id, 
            course_name = course_name,
            run_num = run_num, 
            seconds = seconds, 
            cones = cones, 
            wd = wd, 
            is_redirect=is_redirect
        )
    
@app.route('/add_driver', methods=['GET', 'POST'])
def add_driver():
    connection = getCursor()
    car_query = 'SELECT car_num, model FROM car;'
    course_query = 'SELECT course_id, name FROM course;'
    caregiver_query = """
        SELECT driver_id, CONCAT(first_name, " ", surname) AS name 
        FROM driver 
        WHERE age > 25
        OR age is NULL;
    """
    connection.execute(car_query)
    car_list = connection.fetchall()

    connection.execute(course_query)
    course_list = connection.fetchall()
    
    connection.execute(caregiver_query)
    caregiver_list = connection.fetchall()

    if request.method == 'POST':
        first_name = request.form['first_name']
        surname = request.form['surname']
        car = request.form['car']
        date_of_birth = request.form.get('date_of_birth')
        caregiver = request.form.get('caregiver')
        age = None
        is_not_caregiver = False

        if caregiver is None:
            is_not_caregiver = True
            print('No caregiver')
        else:
            is_not_caregiver = False
            print('Has caregiver')

        if date_of_birth:
            age = calculate_age(date_of_birth)
            error_message = add_driver_form_validation(age, is_not_caregiver, date_of_birth)
            
            if len(error_message) != 0:
                return render_template('routes/admin/addDriver.html', 
                                car_list = car_list, 
                                course_list = course_list,
                                caregiver_list = caregiver_list,
                                error_message = error_message)
            else:  
                add_driver_to_db(first_name, surname, date_of_birth, age, caregiver, car)
                return redirect('/run_search')
        else:
            add_driver_to_db(first_name, surname, date_of_birth, age, caregiver, car)
            return redirect('/run_search')
    
    return render_template('routes/admin/addDriver.html', 
                           car_list = car_list, 
                           course_list = course_list,
                           caregiver_list = caregiver_list
                        )
