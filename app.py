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
    courseList = connection.fetchall()
    return render_template('courselist.html', course_list = courseList)

@app.route('/driver/<driver_id>', methods=['POST', 'GET'])
def driver(driver_id):
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

    return render_template('driverDetails.html', driver = driver_info, runs = run_details)

@app.route('/listdrivers', methods=['GET'])
def listdrivers():
    connection = getCursor()
    query = 'SELECT * FROM driver, car WHERE driver.car = car.car_num;'
    connection.execute(query)
    driverList = connection.fetchall()
    print(driverList)
    return render_template('driverlist.html', driver_list = driverList)    


@app.route('/graph')
def showgraph():
    connection = getCursor()
    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '

    return render_template('top5graph.html', name_list = bestDriverList, value_list = resultsList)

