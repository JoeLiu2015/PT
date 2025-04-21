@echo off
:: User can configure the Python path here
set PYTHON_PATH=C:\Program Files\Python312\python.exe
:: User can configure the location of the pt module here (directory path)
set PT_PATH=..\..\PT

:: Check if the configured Python path exists
if not exist "%PYTHON_PATH%" (
    echo Error: The configured Python path "%PYTHON_PATH%" does not exist.
    exit /b 1
)

:: Check if the configured pt module directory exists
if not exist "%PT_PATH%" (
    echo Error: The pt module directory "%PT_PATH%" does not exist.
    exit /b 1
)

:: If both paths exist, execute the pt module with Python
:: echo Using Python path "%PYTHON_PATH%" to execute the pt module from "%PT_PATH%"...
"%PYTHON_PATH%" "%PT_PATH%" %*