@echo off
echo =========================================
echo Brian Getenga Portfolio - Quick Setup
echo =========================================
echo.

REM Check Python
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo Dependencies installed
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo .env file created
    echo.
    echo IMPORTANT: Please update the following in your .env file:
    echo    - SECRET_KEY
    echo    - EMAIL_HOST_USER
    echo    - EMAIL_HOST_PASSWORD
    echo.
) else (
    echo .env file already exists
    echo.
)

REM Create logs directory
if not exist logs mkdir logs
echo Logs directory created
echo.

REM Run migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate
echo Migrations completed
echo.

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput
echo Static files collected
echo.

REM Create superuser
echo =========================================
echo Create Admin Account
echo =========================================
echo.
python manage.py createsuperuser
echo.

echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo Next steps:
echo 1. Update email settings in .env file
echo 2. Add your profile image and resume to media folder
echo 3. Run: python manage.py runserver
echo 4. Visit: http://127.0.0.1:8000
echo 5. Admin panel: http://127.0.0.1:8000/admin
echo.
echo For deployment instructions, see DEPLOYMENT.md
echo.
echo Happy coding!
echo.

pause
