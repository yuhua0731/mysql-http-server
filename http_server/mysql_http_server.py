#!/usr/bin/env python3
import mysql.connector
from mysql.connector import errorcode
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json


try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="yu",
        password="huayu364+",
        database="test",
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
    return f"(0x{data[0].hex()}, 0x{data[1].hex()}, {data[2].decode()}, {False if data[3] == b'0' else True})"


def print_table(table_name):
    sql = "SELECT * FROM {}".format(table_name)
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    for row in myresult:
        print(print_row(row))


def insert_table(table_name, data):
    sql = "INSERT INTO " + table_name + \
        " (rf_address, operator, st_uid) VALUES (%(rf_address)s, %(operator)s, %(st_uid)s)"
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
        next_rf = int('C32100', 16)
        response_dict = {
                "emb http server": "hello!",
                "supported operations": {
                    "rf_get": "to get a rf address for current shuttle",
                    "rf_confirm": "to confirm that the rf address has been accepted"
                },
                "rf_get example": {
                    "operation": "rf_get",
                    "st_uid": "0x111111222222333333444444",
                    "operator": "yu"
                },
                "rf_confirm example": {
                    "operation": "rf_confirm",
                    "rf_addr": "0xc32100",
                    "st_uid": "0x111111222222333333444444",
                    "operator": "yu"
                }
            }
        if 'operation' in query_components:
            if 'operator' not in query_components:
                print(f"ERROR: access denied for unknown operator")
                response_dict = {
                    "result": "ERROR: access denied, please provide operator's name"
                }
            else:
                if query_components['operation'][0] == 'rf_get':
                    uid = int(query_components['st_uid'][0]).to_bytes(12, byteorder='big', signed=False) # 12-byte uid
                    operator = query_components['operator'][0]
                    mydb.commit()
                    # get current max rf address
                    sql = "SELECT * FROM rfaddr ORDER BY rf_address DESC LIMIT 1"
                    mycursor.execute(sql)
                    # the row count cannot be known before the rows have been fetched 
                    myresult = mycursor.fetchone()
                    # check if table is empty
                    next_rf = int.from_bytes(myresult[0], byteorder='big', signed=False) + 1 if mycursor.rowcount != 0 else int('C32100', 16)
                    next_rf = next_rf.to_bytes(3, byteorder='big', signed=False)
                    print(f"next rf: 0x{next_rf.hex()}")

                    # insert and assign next rf address
                    insert_table("rfaddr", {"rf_address": next_rf, "operator": operator, "st_uid": uid})

                    # print the row just been inserted
                    sql = "SELECT * FROM rfaddr ORDER BY rf_address DESC LIMIT 1"
                    mycursor.execute(sql)
                    myresult = mycursor.fetchone()
                    print(f"row with max rf: {print_row(myresult)}")
                    response_dict = {
                        "rf": f"0x{myresult[0].hex()}",
                        "st_uid": f"0x{myresult[1].hex()}",
                        "operator": myresult[2].decode(),
                        "status": False if myresult[3] == b'0' else True
                    }
                elif query_components['operation'][0] == 'rf_confirm':
                    rf = int(query_components['rf_addr'][0]).to_bytes(3, byteorder='big', signed=False).hex()
                    uid = int(query_components['st_uid'][0]).to_bytes(12, byteorder='big', signed=False).hex()
                    mydb.commit()
                    # get row to be confirmed
                    sql = f"SELECT * FROM rfaddr WHERE rf_address = X'{rf}'"
                    mycursor.execute(sql)
                    myresult = mycursor.fetchone()
                    # check if rf_address exists
                    if mycursor.rowcount != 0:
                        print(f"row to be confirmed: {print_row(myresult)}")
                        if uid != myresult[1].hex():
                            print("ERROR: incorrect st_uid")
                            response_dict = {
                                "result": f"ERROR: incorrect st_uid, should be 0x{myresult[1].hex()}",
                                "rf": f"0x{myresult[0].hex()}",
                                "st_uid": f"0x{myresult[1].hex()}",
                                "operator": myresult[2].decode(),
                                "status": False if myresult[3] == b'0' else True
                            }
                        else:
                            # print the row just been modified
                            sql = f"UPDATE rfaddr SET status = '{1}' WHERE rf_address = X'{rf}'"
                            mycursor.execute(sql)
                            mydb.commit()
                            print(mycursor.rowcount, "record(s) affected")
                            # get row confirmed
                            sql = f"SELECT * FROM rfaddr WHERE rf_address = X'{rf}'"
                            mycursor.execute(sql)
                            myresult = mycursor.fetchone()
                            print(f"row confirmed: {print_row(myresult)}")
                            response_dict = {
                                "result": "rf_addr confirmed",
                                "rf": f"0x{myresult[0].hex()}",
                                "st_uid": f"0x{myresult[1].hex()}",
                                "operator": myresult[2].decode(),
                                "status": False if myresult[3] == b'0' else True
                            }
                    else:
                        print(f"ERROR: cannot find rf: {rf}")
                        response_dict = {
                            "result": "ERROR: cannot find rf"
                        }

        self._set_headers()
        self.wfile.write(self._encode(json.dumps(response_dict, indent=4, sort_keys=False)))


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
    # start http server
    parser = argparse.ArgumentParser(description = "Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
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
