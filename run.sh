#!/usr/bin/env bash
set -e

cd cbsapi && uwsgi \
                --http :5000  \
                --wsgi-file cbsapi.py \
                --callable app \
                --master \
                --processes 8 \
                --cheaper 2 \
                --lazy-apps \
                --need-app \
                --enable-threads \
                --disable-logging
