## Introduction
API service for booking tickets and tracking flights from airports across the whole globe.
## Getting Started
Install PostgresSQL and create db.
1. Clone the repository:
'''
https://github.com/ladno338/airport.git
'''
2. Navigate to the project directory:
'''
cd airport_api
'''
3. Switch to the develop branch:
'''
git checkout develop
'''
4. Create a virtual environment:
'''
python -m venv venv
'''
5. Activate the virtual environment:
'''
python -m venv venv
'''
6. Install project dependencies:
'''
pip install -r requirements.txt
'''
7. Copy .env.sample to .env and populate it with all required data.
8. Run database migrations:
'''
python manage.py migrate
'''
9. Start the development server:
'''
python manage.py runserver
'''
## Main features
1. JWT Authentication
2. Email-Based Authentication
3. Admin panel
4. Throttling Mechanism
5. API documentation
6. Creating airplane with Image
7. Filtering for Flights and Routs
8. Implement a new permission class
