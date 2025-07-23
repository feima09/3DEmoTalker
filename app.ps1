.\python\python.exe -m pip config set global.index-url https://pypi.org/simple
# .\python\python.exe -m pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

.\python\python.exe -m pip install --upgrade pip
.\python\python.exe -m pip install -r requirements.txt

Start-Sleep -Seconds 3

.\python\python.exe app.py

Read-Host -Prompt "Press Enter to exit"
