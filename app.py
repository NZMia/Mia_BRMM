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
  
def custom_sort_key(item):
    overall_total = item[1]['overall_total']
    if overall_total == 'NQ':
        return float('inf')  # Assign a larger value to 'NQ'
    return float(overall_total)

@app.route('/overallresults', methods=['GET'])
def overallresults():
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
                car.model, 
                car.car_num,
                c.course_id,
                c.name as course_name,
                r.seconds +
                COALESCE(5 * r.cones, 0) +
                COALESCE(10 * r.wd, 0) AS run_total,
                ROW_NUMBER() OVER (PARTITION BY d.driver_id, c.course_id ORDER BY COALESCE(r.seconds, 99999)) AS row_num
            FROM driver AS d
            JOIN run AS r ON d.driver_id = r.dr_id
            JOIN course AS c ON r.crs_id = c.course_id
            JOIN car AS car ON d.car = car.car_num
        )

        SELECT 
            driver_id,
            name,
            model,
            course_id,
            CASE
                WHEN COALESCE(run_total, 0) = 0 THEN 'dnf'
                ELSE FORMAT(run_total, 2)
            END AS course_time
        FROM RankedData
        WHERE row_num = 1
        ORDER BY driver_id, course_id;
    """
    connection.execute(query)
    original_data = connection.fetchall()
    output_data = {}
    course_times_dic = {}
    output_data_overall = {}
    overall_results_dic ={}
    for item in original_data:
        driver_id, name, model, course_id, course_time = item
        key = (driver_id, name, model)
        value = [
            {course_id: course_time}
        ]
        if key not in course_times_dic.keys():
             course_times_dic[key] = value
        else:
            if course_id not in course_times_dic[key]:
                course_times_dic[key].append({course_id: course_time})

    for item in original_data:
        key = item[:3]
        value = float(item[-1]) if item[-1] != 'dnf' else 'NQ'

        if key not in overall_results_dic.keys():
            overall_results_dic[key] = value
        else:
            if value != 'NQ':
                overall_results_dic[key] += value

                round(overall_results_dic[key], 2)
            else:
                overall_results_dic[key] = 'NQ'
                
    print (course_times_dic)
    print (overall_results_dic)
    # output_list = [(
    #     id, name, model, data_dict, 
    #     round(sum(float(v) for v in data_dict.values()), 2)) if data_dict.get(1) is not 'dnf' else 'NQ'
    #     for id, name, model, data_dict in output_data.values()]

    # for id, name, model, data_dict in output_data.values():
    #     overall = 0
    #     if data_dict.get(1) is 'dnf':
    #         overall = 'NQ'
    #     else:
            # overall = round(sum(float(v) for v in data_dict.values()), 2)
    # print(output_list)
    return render_template('routers/visiter/overallResults.html', rank_list = original_data)

@app.route('/graph')
def showgraph():
    connection = getCursor()
    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '

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

