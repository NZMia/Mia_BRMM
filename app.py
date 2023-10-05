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
    return render_template('base.html')

@app.route('/listcourses', methods=['GET'])
def listcourses():
    connection = getCursor()
    connection.execute('SELECT * FROM course;')
    courseList = connection.fetchall()
    return render_template('courselist.html', course_list = courseList)

@app.route('/driver/<driver_id>', methods=['POST', 'GET'])
def driver(driver_id):
    connection = getCursor()
    connection.execute(
        'SELECT * FROM driver, run, car, course WHERE driver.driver_id = run.dr_id AND run.crs_id = course.course_id AND driver.car = car.car_num AND driver.driver_id = %s;', 
        (driver_id,)
    )
    driver = connection.fetchall()
    print(driver)
    return render_template('driver.html', driver = driver)

@app.route('/listdrivers', methods=['GET'])
def listdrivers():
    connection = getCursor()

    connection.execute('SELECT * FROM driver, car WHERE driver.car = car.car_num;')
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

