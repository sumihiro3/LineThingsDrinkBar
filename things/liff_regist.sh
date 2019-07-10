#!/usr/bin/env bash

curl -X POST https://api.line.me/things/v1/trial/products \
-H 'Authorization: Bearer gJhGY0QpKvarghG2IoTlqPzvV9c4mjn/QBBIJfnGqyBjq8PoT0nwvzsu+fu2NXiTLDlJgx3DAraCOZlKg0XJdj7cJkLOGVPRFra5CFPiFxF4ve7BNTKNFvFrs7ThEIJXPE5BHnxNl1fFbqOcoq5OLAdB04t89/1O/w1cDnyilFU=' \
-H 'Content-Type:application/json' \
-d '{
  "name": "LINE Things Drink dispenser",
  "liffId": "1597172191-jezrKZRq"
}'
