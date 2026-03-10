@echo off
echo Оновлюю pip...
python -m pip install --upgrade pip setuptools wheel

echo Встановлюю psutil...
python -m pip install psutil

echo Встановлюю pywin32...
python -m pip install pywin32

echo Запускаю postinstall для pywin32...
python %~dp0\..\..\Scripts\pywin32_postinstall.py -install

echo ================================
echo ✅ Установка завершена!
pause