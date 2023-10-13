from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime

import mysql.connector
from mysql.connector import FieldType
import connect_local

app = Flask(__name__)

dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect_local.dbuser, \
    password=connect_local.dbpass, host=connect_local.dbhost, \
    database=connect_local.dbname, autocommit=True)
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

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/listcourses', methods=['GET'])
def listcourses():
    connection = getCursor()
    connection.execute('SELECT * FROM course ORDER BY course.course_id;')
    course_list = connection.fetchall()
    return render_template('routers/visiter/courseList.html', course_list = course_list)

@app.route('/driverdetails/', methods=['GET'])
def driverdetails():
    driver_id = request.args.get('driver_id')
    connection = getCursor()

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

    return render_template('routers/visiter/driverDetails.html', driver = driver_info, runs = run_details)

@app.route('/listdrivers', methods=['GET'])
def listdrivers():
    connection = getCursor()
    query = 'SELECT * FROM driver, car WHERE driver.car = car.car_num;'
    connection.execute(query)
    driverList = connection.fetchall()
    print(driverList)
    return render_template(
        'routers/visiter/driverList.html',
        driver_list = driverList
    )  

@app.route('/overallresults', methods=['GET'])
def overallresults():

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
    
    print (course_times_dic)

    return render_template('routers/visiter/overallResults.html', rank_list = course_times_dic)

@app.route('/graph')
def graph():
    # original_data
    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '
# name_list = bestDriverList, value_list = resultsList  
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

    print(bestDriverList)
    print(resultsList)
    return render_template('routers/visiter/top5graph.html', name_list = bestDriverList, value_list = resultsList)





@app.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')

@app.route('/juniorList', methods=['GET'])
def juniorList():
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
    print(junior_list)
    return render_template('routers/admin/juniorList.html', junior_list = junior_list) 

@app.route('/driversearch', methods=['GET', 'POST'])
def driversearch():
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
    
    return render_template('routers/admin/driverSearch.html', driver_info = driver_info, show_results = show_results)

@app.route('/runsearch', methods=['GET', 'POST'])
def runsearch():
    run_info = []
    show_results = False
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

    driver_id = request.args.get('driver_id')
    course_id = request.args.get('course_id')

    if driver_id is not None:
        driver_run_query = """
            SELECT  d.driver_id, concat(d.first_name, ' ', d.surname) as name, r.crs_id, r.run_num, r.seconds, r.cones, r.wd
            FROM driver as d
                JOIN run as r on r.dr_id = d.driver_id
            WHERE d.driver_id = %s;
        """

        connection.execute(driver_run_query, (driver_id,))
        run_info = connection.fetchall()
        show_results = True
  
    if course_id is not None:
        course_run_query = """ 
            SELECT c.course_id, c.name, r.dr_id, r.run_num, r.seconds, r.cones, r.wd
            FROM course as c
                JOIN run as r on r.crs_id = c.course_id
            WHERE c.course_id = %s;
        """
        connection.execute(course_run_query, (course_id,))
        run_info = connection.fetchall()
        show_results = True
    print(run_info)
    return render_template(
        'routers/admin/editRun.html',
        driver_run_info = driver_run_info,
        course_details = course_details,
        run_info = run_info, 
        show_results = show_results
    )