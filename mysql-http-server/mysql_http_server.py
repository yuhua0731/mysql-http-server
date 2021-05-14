#!/usr/bin/env python3
import subprocess
import sys
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import socket

try:
    import mysql.connector
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", 'mysql-connector-python'])
finally:
    import mysql.connector
    from mysql.connector import errorcode

try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="rfaddr_db",
        raw=True
    )
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
else:
    mycursor = mydb.cursor()


def print_row(data):
    return f"(0x{data[0].hex()}, {int(data[1].decode())}, {int(data[2].decode())}, {int(data[3].decode())}, {data[4].decode()}, {False if data[5] == b'0' else True})"


def print_table(table_name):
    sql = "SELECT * FROM {}".format(table_name)
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    for row in myresult:
        print(print_row(row))


def insert_table(table_name, data):
    sql = "INSERT INTO " + table_name + \
        " (rf_address, operator, st_uid_1, st_uid_2, st_uid_3) VALUES (%(rf_address)s, %(operator)s, %(st_uid_1)s, %(st_uid_2)s, %(st_uid_3)s)"
    mycursor.execute(sql, data)
    mydb.commit()
    print(mycursor.rowcount, "record inserted.")


def clear_result():
    mycursor.fetchall()


# simple http server, can only response to GET request with argument 'st_uid'
class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def _encode(self, message):
        # This generates a json object
        return message.encode("utf-8")  # NOTE: must return a bytes object!

    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        next_rf = int('A32B00', 16)
        # to do
        response_dict = {
            "emb http server": "hello!",
            "supported operations": {
                "get_rf_address": "to get a rf address for current shuttle",
                "confirm_rf_address": "to confirm that the rf address has been accepted"
            },
            "get_rf_address example": {
                "operation": "get_rf_address",
                "st_uid0": "456435",
                "st_uid1": "56431",
                "st_uid2": "654456",
                "operator": "yu"
            },
            "confirm_rf_address example": {
                "operation": "confirm_rf_address",
                "rf_address": "A32B00",
                "st_uid0": "456435",
                "st_uid1": "56431",
                "st_uid2": "654456",
                "flash_result": "OK",
                "operator": "yu"
            }
        }
        if 'operation' in query_components:
            if query_components['operation'][0] == 'get_rf_address':
                if 'operator' not in query_components:
                    print(f"ERROR: access denied, need operator's name")
                    response_dict = {
                        "result": "ERROR: access denied, need operator's name"
                    }
                else:
                    uid = [int(query_components['st_uid0'][0]), int(
                        query_components['st_uid1'][0]), int(query_components['st_uid2'][0])]
                    operator = query_components['operator'][0]
                    mydb.commit()
                    # get current max rf address
                    sql = "SELECT * FROM rfaddr ORDER BY rf_address DESC LIMIT 1"
                    mycursor.execute(sql)
                    # the row count cannot be known before the rows have been fetched
                    myresult = mycursor.fetchone()
                    # check if table is empty
                    next_rf = int.from_bytes(
                        myresult[0], byteorder='big', signed=False) + 1 if mycursor.rowcount != 0 else int('A32B00', 16)
                    next_rf = next_rf.to_bytes(
                        3, byteorder='big', signed=False)
                    print(f"next rf: {next_rf.hex()}")

                    # insert and assign next rf address
                    insert_table("rfaddr", {"rf_address": next_rf, "operator": operator,
                                            "st_uid_1": uid[0], "st_uid_2": uid[1], "st_uid_3": uid[2]})

                    # print the row just been inserted
                    sql = "SELECT * FROM rfaddr ORDER BY rf_address DESC LIMIT 1"
                    mycursor.execute(sql)
                    myresult = mycursor.fetchone()
                    fetchuid = [int(myresult[1].decode()), int(
                        myresult[2].decode()), int(myresult[3].decode())]
                    print(f"row with max rf: {print_row(myresult)}")
                    response_dict = {
                        "result": "OK",
                        "rf_address": f"{myresult[0].hex()}",
                        "st_uid0": fetchuid[0],
                        "st_uid1": fetchuid[1],
                        "st_uid2": fetchuid[2],
                        "operator": myresult[4].decode(),
                        "status": False if myresult[5] == b'0' else True
                    }
            elif query_components['operation'][0] == 'confirm_rf_address':
                rf = int(query_components['rf_address'][0], 16).to_bytes(
                    3, byteorder='big', signed=False).hex()
                uid = [int(query_components['st_uid0'][0]), int(
                    query_components['st_uid1'][0]), int(query_components['st_uid2'][0])]
                mydb.commit()
                # get row to be confirmed
                sql = f"SELECT * FROM rfaddr WHERE rf_address = X'{rf}'"
                mycursor.execute(sql)
                myresult = mycursor.fetchone()
                # check if rf_address exists
                if mycursor.rowcount != 0:
                    fetchuid = [int(myresult[1].decode()), int(
                        myresult[2].decode()), int(myresult[3].decode())]
                    if 'operator' not in query_components:
                        print(f"ERROR: access denied, need operator's name")
                        response_dict = {
                            "result": "ERROR: access denied, need operator's name",
                            "rf_address": f"{myresult[0].hex()}",
                            "st_uid0": fetchuid[0],
                            "st_uid1": fetchuid[1],
                            "st_uid2": fetchuid[2],
                            "operator": "",
                            "status": False if myresult[5] == b'0' else True
                        }
                    else:
                        print(f"row to be confirmed: {print_row(myresult)}")
                        if uid[0] != fetchuid[0] or uid[1] != fetchuid[1] or uid[2] != fetchuid[2]:
                            print("ERROR: incorrect st_uid")
                            response_dict = {
                                "result": f"ERROR: incorrect st_uid, should be {fetchuid[0]}, {fetchuid[1]}, {fetchuid[2]}",
                                "rf_address": f"{myresult[0].hex()}",
                                "st_uid0": fetchuid[0],
                                "st_uid1": fetchuid[1],
                                "st_uid2": fetchuid[2],
                                "operator": myresult[4].decode(),
                                "status": False if myresult[5] == b'0' else True
                            }
                        else:
                            if query_components['flash_result'][0] == 'OK':
                                # update row
                                sql = f"UPDATE rfaddr SET status = '{1}' WHERE rf_address = X'{rf}'"
                                mycursor.execute(sql)
                                mydb.commit()
                                print(mycursor.rowcount, "record(s) affected")
                                # get row confirmed
                                sql = f"SELECT * FROM rfaddr WHERE rf_address = X'{rf}'"
                                mycursor.execute(sql)
                                myresult = mycursor.fetchone()
                                print(f"row confirmed: {print_row(myresult)}")
                            else:
                                print("flash failed")
                            response_dict = {
                                "result": "OK",
                                "rf_address": f"{myresult[0].hex()}",
                                "st_uid0": fetchuid[0],
                                "st_uid1": fetchuid[1],
                                "st_uid2": fetchuid[2],
                                "operator": myresult[4].decode(),
                                "status": False if myresult[5] == b'0' else True
                            }
                else:
                    print(f"ERROR: cannot find rf: {rf}")
                    response_dict = {
                        "result": "ERROR: cannot find rf"
                    }

        self._set_headers()
        self.wfile.write(self._encode(json.dumps(
            response_dict, indent=4, sort_keys=False)))


def run(server_class=HTTPServer, handler_class=S, addr='localhost', port=8000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
    print(f'Started httpd server on {addr}:{port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    mycursor.close()
    print('Stopped httpd and cursor')


def main():
    host_addr = socket.gethostbyname(socket.gethostname(
    )) if sys.platform == "darwin" else socket.gethostbyname(socket.gethostname() + ".local")

    # start http server
    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default=host_addr,
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)


if __name__ == "__main__":
    main()
