./mysql_http_client_para1.py -l http://10.0.20.50:8000/ -u yu -p /dev/tty.usbmodem141403 &  p1=$!
./mysql_http_client_para2.py -l http://10.0.20.50:8000/ -u yu -p /dev/tty.usbmodem141403 &  p2=$!
./mysql_http_client_para3.py -l http://10.0.20.50:8000/ -u yu -p /dev/tty.usbmodem141403 &  p2=$!
wait $p1
wait $p2
wait $p3
