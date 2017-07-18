def update_script(replacetxt, filename):
    import re
    with open(filename, 'r') as file:
        filedata = file.read()
        # Replace the target string
    reg = re.compile(r'"\d{3}"')
    filedata = re.sub(reg, replacetxt, filedata)
    # Write the file out again
    with open(filename, 'w') as file:
        file.write(filedata)


def purge_zero_records(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM STATS_DAILY WHERE ACD_CALLS = 0 AND AVAIL_TIME = 0")
    conn.commit()


def get_agents(conn, products):
    products = [str(x) for x in products]
    pp = [', '.join(products)]
    cur = conn.cursor()
    cur.execute("SELECT FIRSTNAME, LASTNAME, AGENT_ID FROM AGENTS WHERE PRODUCT_ID IN (" + pp[0] + ")")
    data = cur.fetchall()
    return data

def get_cms_names(conn):
    cur = conn.cursor()
    cur.execute("SELECT CMS_NAME, AGENT_ID FROM AGENTS ORDER BY AGENT_ID")
    data = cur.fetchall()
    return data

def update_date(replacetxt, filename):
    import re
    with open(filename, 'r') as file:
        filedata = file.read()
        # Replace the target string
    regex = r"\d{2}/\d{2}/\d{2}"
    filedata = re.sub(regex, replacetxt, filedata)
    # Write the file out again
    with open(filename, 'w') as file:
        file.write(filedata)


def get_newest_date(db):
    import sqlite3
    cur = db.cursor()
    cur.execute("SELECT MAX(DATE) FROM STATS_DAILY WHERE ACD_CALLS > 0")
    date = cur.fetchall()
    db.commit()
    return date


def read_data(filename, rundate, queue_id):
    import csv, sqlite3

    queues = {1: 471, 2: 487, 3: 485}
    queue_ids = {471: 1, 487: 2, 485: 3}
    conn = sqlite3.connect('phone.db')
    agents = get_cms_names(conn)
    '''agents = [(1, 'Jake Brn', 'Kinsey'),
              (2, 'Josh', 'Ard'),
              (3, 'James', 'Dykes'),
              (4, 'Alexander', 'Cunningham'),
              (5, 'David', 'Gorman'),
              (6, 'Evan', 'Tomboulian'),
              (7, 'Pramod', 'Neelambaran'),
              (8, 'Chance', 'Tutt'),
              (9, 'Matthew Tech', 'Reed'),
              (10, 'Edward', 'Tan'),
              (11, 'Jason', 'Cheung'),
              (12, 'Patrick', 'Savage'),
              (13, 'Emmanuel', 'Salter'),
              (14, 'Jake', 'Nelson'),
              (15, 'Andrew', 'Billups'),
              (16, 'Gabriel', 'Lam'),
              (17, 'Leon', 'Zhang'),
              (18, 'Danny', 'Han'),
              (19, 'Houston', 'Hardaway'),
              (20, 'Tremahne', 'Lockhart'),
              (21, 'Lee', 'Perina'),
              (22, 'Ali', 'Lopez'),
              (23, 'Katherine', 'Jacobi'),
              (24, 'Frank', 'Buttafarro'),
              (25, 'Matthew', 'Hui'),
              (26, 'Stephen', 'Gray'),
              (27, 'David', 'Kreiner'),
              (28, 'Rosely', 'Bolio'),
              (29, 'Jasmeet', 'Lail'),
              (30, 'Julius', 'Dagot'),
              (31, 'Harrison', 'Booth'),
              (32, 'Casey', 'Jackson'),
              (33, 'Keith', 'Reville')]'''
    # format names
    agents2 = [x[0] for x in agents]
    # read data from file
    with open(filename, 'r') as file:
        csvreader = csv.reader(file, delimiter=';')
        data = list(csvreader)
        # queue_id = queue_ids[int(data[1][1])]
        data = data[2:]

    # change agent name into agent ID
    for row in data[2:]:
        row[0] = agents2.index(row[0]) + 1

    # prepare query
    headers = data[0]
    data = data[2:]
    headers[0] = "AGENT_ID"
    for e in range(len(headers)):
        headers[e] = headers[e].upper()
        headers[e] = headers[e].replace(" ", "_")
    for i in range(len(data)):
        data[i] = [rundate.strftime("%Y-%m-%d"), queue_id] + data[i]
    temp = ", ".join(headers)
    query = "INSERT INTO STATS_DAILY ( DATE, QUEUE_ID, " + temp + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    return (query, data)


def weekly_data(conn):
    import sqlite3
    query = "SELECT A.FIRSTNAME || ' ' || A.LASTNAME NAME,\
        strftime('%Y-%W',sd.date) WEEK,\
        min(date) START_DATE,\
        max(date) END_DATE,\
        SUM(ACD_CALLS) CALLS,\
        ROUND(SUM(AVG_ACD_TIME * ACD_CALLS) / SUM(ACD_CALLS) /60.0,2  ) AVG_CALL_LENGTH,\
        ROUND(SUM(AVG_ACW_TIME * ACD_CALLS) / SUM(ACD_CALLS) /60.0,2  ) AVG_AFTER_CALL,\
        ROUND(SUM(AGENT_RING_TIME) / SUM(ACD_CALLS) , 1  ) AVG_RING_TIME,\
        ROUND(CAST(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN AUX_TIME ELSE 0 END ) AS FLOAT) / SUM(ACD_CALLS) /60.0,2 ) AUX_TIME_PER_CALL,\
        ROUND(CAST(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN AVAIL_TIME ELSE 0 END ) AS FLOAT) / SUM(ACD_CALLS) /60.0,2 ) AVG_AVAIL_TIME,\
        ROUND(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN STAFFED_TIME ELSE 0 END )/ CAST(COUNT(DISTINCT DATE) AS FLOAT) / 3600.0, 2 ) STAFFED_PER_DAY,\
        SUM(HELD_CALLS) HELD_CALLS ,\
        CAST( CAST(SUM(HELD_CALLS) AS FLOAT) / sum(ACD_CALLS) * 100.0 AS INT)  HOLD_RATIO,\
        IFNULL(ROUND (CAST(SUM(AVG_HOLD_TIME * HELD_CALLS) AS FLOAT) / CAST(SUM(HELD_CALLS) AS FLOAT) /60.0, 2 ),0)  AVG_HOLD_LENGTH\
        FROM STATS_DAILY SD JOIN AGENTS A ON SD.AGENT_ID = A.AGENT_ID\
        WHERE sd.QUEUE_ID <> 3 and A.ACTIVE = 1 and A.PRODUCT_ID = 1\
        GROUP BY 2,1\
        HAVING SUM(ACD_CALLS) > 0\
        order by 1,2"

    columns = ['name','week','start_date',
               'end_date','calls','avg_call_length',
               'avg_after_call','avg_ring_time',
               'aux_time_per_call','avg_avail_time','staffed_per_day',
               'held_calls','hold_ratio','avg_hold_time']

    cur = conn.cursor()

    cur.execute(query)

    return cur.fetchall(),columns

def daily_data(conn):
    import sqlite3
    query = "SELECT A.FIRSTNAME || ' ' || A.LASTNAME NAME,\
        strftime('%Y-%m-%d',sd.date) DAY,\
        min(date) START_DATE,\
        SUM(ACD_CALLS) CALLS,\
        ROUND(SUM(AVG_ACD_TIME * ACD_CALLS) / SUM(ACD_CALLS) /60.0,2  ) AVG_CALL_LENGTH,\
        ROUND(SUM(AVG_ACW_TIME * ACD_CALLS) / SUM(ACD_CALLS) /60.0,2  ) AVG_AFTER_CALL,\
        ROUND(SUM(AGENT_RING_TIME) / SUM(ACD_CALLS) , 1  ) AVG_RING_TIME,\
        ROUND(CAST(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN AUX_TIME ELSE 0 END ) AS FLOAT) / SUM(ACD_CALLS) /60.0,2 ) AUX_TIME_PER_CALL,\
        ROUND(CAST(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN AVAIL_TIME ELSE 0 END ) AS FLOAT) / SUM(ACD_CALLS) /60.0,2 ) AVG_AVAIL_TIME,\
        ROUND(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN STAFFED_TIME ELSE 0 END )/ CAST(COUNT(DISTINCT DATE) AS FLOAT) / 3600.0, 2 ) STAFFED_PER_DAY,\
        SUM(HELD_CALLS) HELD_CALLS ,\
        CAST( CAST(SUM(HELD_CALLS) AS FLOAT) / sum(ACD_CALLS) * 100.0 AS INT)  HOLD_RATIO,\
        IFNULL(ROUND (CAST(SUM(AVG_HOLD_TIME * HELD_CALLS) AS FLOAT) / CAST(SUM(HELD_CALLS) AS FLOAT) /60.0, 2 ),0)  AVG_HOLD_LENGTH\
        FROM STATS_DAILY SD JOIN AGENTS A ON SD.AGENT_ID = A.AGENT_ID\
        WHERE sd.QUEUE_ID <> 3 and A.ACTIVE = 1 and A.PRODUCT_ID = 1\
        GROUP BY 2,1\
        HAVING SUM(ACD_CALLS) > 0\
        order by 1,2"

    columns = ['name','day','start_date',
               'calls','avg_call_length',
               'avg_after_call','avg_ring_time',
               'aux_time_per_call','avg_avail_time','staffed_per_day',
               'held_calls','hold_ratio','avg_hold_time']

    cur = conn.cursor()

    cur.execute(query)

    return cur.fetchall(),columns


def monthly_data(conn):
    import sqlite3
    query = "SELECT A.FIRSTNAME || ' ' || A.LASTNAME NAME,\
        strftime('%Y-%m',sd.date) MONTH,\
        strftime('%Y-%m',sd.date) START_DATE,\
        max(date) END_DATE,\
        SUM(ACD_CALLS) CALLS,\
        ROUND(SUM(AVG_ACD_TIME * ACD_CALLS) / SUM(ACD_CALLS) /60.0,2  ) AVG_CALL_LENGTH,\
        ROUND(SUM(AVG_ACW_TIME * ACD_CALLS) / SUM(ACD_CALLS) /60.0,2  ) AVG_AFTER_CALL,\
        ROUND(SUM(AGENT_RING_TIME) / SUM(ACD_CALLS) , 1  ) AVG_RING_TIME,\
        ROUND(CAST(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN AUX_TIME ELSE 0 END ) AS FLOAT) / SUM(ACD_CALLS) /60.0,2 ) AUX_TIME_PER_CALL,\
        ROUND(CAST(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN AVAIL_TIME ELSE 0 END ) AS FLOAT) / SUM(ACD_CALLS) /60.0,2 ) AVG_AVAIL_TIME,\
        ROUND(SUM(CASE WHEN QUEUE_ID IN (1,3) THEN STAFFED_TIME ELSE 0 END )/ CAST(COUNT(DISTINCT DATE) AS FLOAT) / 3600.0, 2 ) STAFFED_PER_DAY,\
        SUM(HELD_CALLS) HELD_CALLS ,\
        CAST( CAST(SUM(HELD_CALLS) AS FLOAT) / sum(ACD_CALLS) * 100.0 AS INT)  HOLD_RATIO,\
        IFNULL(ROUND (CAST(SUM(AVG_HOLD_TIME * HELD_CALLS) AS FLOAT) / CAST(SUM(HELD_CALLS) AS FLOAT) /60.0, 2 ),0)  AVG_HOLD_LENGTH\
        FROM STATS_DAILY SD JOIN AGENTS A ON SD.AGENT_ID = A.AGENT_ID\
        WHERE sd.QUEUE_ID <> 3 and A.ACTIVE = 1 and A.PRODUCT_ID = 1\
        GROUP BY 1,2\
        HAVING SUM(ACD_CALLS) > 0\
        order by 1,2"

    columns = ['name','month','start_date',
               'end_date','calls','avg_call_length',
               'avg_after_call','avg_ring_time',
               'aux_time_per_call','avg_avail_time','staffed_per_day',
               'held_calls','hold_ratio','avg_hold_time']

    cur = conn.cursor()

    cur.execute(query)

    return cur.fetchall(),columns