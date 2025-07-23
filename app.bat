@echo off

python\python.exe -m pip config set global.index-url https://pypi.org/simple

@REM python\python.exe -m pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

python\python.exe -m pip install --upgrade pip

python\python.exe -m pip install -r requirements.txt

ping 127.0.0.1 -n 3 >nul

python\python.exe app.py 2>&1

@pause
