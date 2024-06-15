import sqlite3
import time

data_path = '/home/gunicorn/data.db'

def create_db():
    try:
        con = sqlite3.connect(data_path)
        cur = con.cursor()
        cur.execute("CREATE TABLE vara(id, running_id, finished_time)")
        cur.execute("INSERT INTO vara VALUES(0, NULL, NULL)")    
        con.commit()
        cur.close()
        con.close()
    except sqlite3.OperationalError:
        return True
    except:
        return False
    return True

def get_data():
    try:
        con = sqlite3.connect(data_path)
        cur = con.cursor()
        res = cur.execute("SELECT running_id, finished_time FROM vara WHERE id=0")
        data = res.fetchone()
        running_id = data[0]
        finished_time = data[1]
        cur.close()
        con.close()
        return True, running_id, finished_time
    except:
        return False, None, None

def update_date(running_id, finished_time):
    try:
        con = sqlite3.connect(data_path)
        cur = con.cursor()
        sql = "UPDATE vara SET "
        if running_id is None:
            sql += "running_id=NULL, "
        else:
            sql += "running_id='%s', " % running_id 
        if finished_time is None:
            sql += "finished_time=NULL "
        else:
            sql += "finished_time=%s " % finished_time
        sql += "WHERE id=0"
        #sql = "UPDATE vara SET running_id='%s' ,finished_time=%s WHERE id=0"% (running_id, finished_time)
        cur.execute(sql)
        con.commit()
        cur.close()
        con.close()
        return True
    except Exception as e:
        #print("reason:", str(e))
        return False

if __name__ == '__main__':
    y = 122
    ok = update_date(None, None)
    #create_db()
    o0, a1, a2 = get_data()
    print(ok)
    print(a1)
    print(a2)
    
