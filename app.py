from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime

import mysql.connector
from mysql.connector import FieldType
import connect

app = Flask(__name__)

dbconn = None
connection = None
is_redirect = False

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn

def getOverallResults():
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
        ),
        RankedDataWithCourseTime AS (
            SELECT 
                driver_id,
                name,
                age,
                model,
                course_id,
                run_total,
                CASE
                    WHEN COALESCE(run_total, 0) = 0 THEN 'dnf'
                    ELSE FORMAT(run_total, 2)
                END AS course_time
            FROM RankedData AS t1
            WHERE row_num = 1
        )

        SELECT 
            driver_id,
            name,
            age,
            model,
            course_id,
            course_time,
            CASE
                WHEN 'dnf' IN (
                    SELECT course_time 
                    FROM RankedDataWithCourseTime AS rdc 
                    WHERE rdc.driver_id = rdc1.driver_id
                ) THEN 'NQ'
                ELSE FORMAT(
                    SUM(
                        CAST(run_total AS DECIMAL(10, 2))
                    ) OVER (PARTITION BY rdc1.driver_id)
                    ,2)
            END AS overall_results
        FROM RankedDataWithCourseTime AS rdc1
        ORDER BY 
            CASE 
                WHEN overall_results = 'NQ' THEN 1
                ELSE 0
            END,
            overall_results,
            course_id;
    """
    connection.execute(query)
    return connection.fetchall()

def getDrivers():
    connection = getCursor()
    query = 'SELECT * FROM driver, car WHERE driver.car = car.car_num;'
    connection.execute(query)
    driverList = connection.fetchall()
    return driverList

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
    driver_list = getDrivers()
    if is_run_details:
        return render_template(
            'routes/visiter/driversDropdown.html',
            driver_list = driver_list,
        )
    else:
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
@app.route('/results', methods=['GET'])
def results():

    original_data = getOverallResults()
    course_times_dic = {}

    for item in original_data:
        driver_id, name, age, model, course_id, course_time, overall_results = item
        key = (driver_id, name, age, model, overall_results)
        value = [
            {course_id: course_time}
        ]
        if key not in course_times_dic.keys():
             course_times_dic[key] = value
        else:
            if course_id not in course_times_dic[key]:
                course_times_dic[key].append({course_id: course_time})

    return render_template('routes/visiter/overallResults.html', rank_list = course_times_dic)

# Route: Top 5 graph
@app.route('/graph')
def graph():
    original_data = getOverallResults()
    bestDriverList = []
    resultsList = []
    unique_output = set()

    for item in original_data:
        if item[0] not in unique_output:
            name = str(item[0]) + ' ' + item[1]
            bestDriverList.append(name)
            resultsList.append(item[-1])
            unique_output.add(item[0])
        if len(unique_output) == 5:
            break
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
        SELECT d.driver_id, concat(d.first_name, ' ', d.surname) as name
        FROM driver as d;
    """
    course_info = """
        SELECT c.course_id, c.name
        FROM course as c;
    """
    connection.execute(driver_info)
    driver_run_info = connection.fetchall()

    connection.execute(course_info)
    course_details = connection.fetchall()

    if request.method == 'POST':
        if 'selected_driver' in request.form:
            driver_id = request.form['selected_driver']
            # Process the selected driver form here
        else:
            course_id = request.form['selected_course']

    if len(driver_id) > 0:
        driver_run_query = """
            SELECT  d.driver_id, concat(d.first_name, ' ', d.surname) as name, r.crs_id, r.run_num, r.seconds, r.cones, r.wd
            FROM driver as d
                JOIN run as r on r.dr_id = d.driver_id
            WHERE d.driver_id = %s;
        """

        connection.execute(driver_run_query, (driver_id,))
        run_info = connection.fetchall()
        show_results = True
  
    if len(course_id) > 0:
        course_run_query = """ 
            SELECT r.dr_id, c.name, c.course_id, r.run_num, r.seconds, r.cones, r.wd
            FROM course as c
                JOIN run as r on r.crs_id = c.course_id
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
        course_id = request.form['course_id']
        run_num = request.form['run_num']
        name = request.form['name']

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
        return render_template('routes/admin/editRun.html', driver_id = driver_id, name = name, course_id = course_id, run_num = run_num, seconds = seconds, cones = cones, wd = wd, is_redirect=is_redirect)
    else:
        
        is_redirect = False
        driver_id = request.args.get('driver_id')
        name = request.args.get('name')
        course_id = request.args.get('course_id')
        run_num = request.args.get('run_num')
        seconds = request.args.get('seconds')
        cones = request.args.get('cones')
        wd = request.args.get('wd')
        
        return render_template('routes/admin/editRun.html', driver_id = driver_id, name = name, course_id = course_id, run_num = run_num, seconds = seconds, cones = cones, wd = wd, is_redirect=is_redirect)
    
@app.route('/add_driver', methods=['GET'])
def add_driver():
    connection = getCursor()
    car_query = 'SELECT car_num, model FROM car;'
    course_query = 'SELECT course_id, name FROM course;'

    connection.execute(car_query)
    car_list = connection.fetchall()

    connection.execute(course_query)
    course_list = connection.fetchall()
    
    run_num = [1, 2]

    return render_template('routes/admin/addDriver.html', 
                           car_list = car_list, 
                           course_list = course_list,
                           run_num=run_num)
