# Automdjango

__Automdjango__ is a python-based testing framework built using Django framework. 

It supports web-based applications currently, and development is in progress to include mobile-based ones.

It uses __Pytest__ as the testing runner.

It uses __Allure__ for reporting test results.

It focuses, at the moment, on testing the application/system using __selenium__ and __page object__ model. 

Later releases would include supporting API testing using REST.

It is __dockerized__ for quick run; Need to have _"__Docker Desktop__"_ as a pre-requisite

## Installation

- Clone the repo into your desired local directory
- Execute the following command in the terminal inside your directory

   ```bash
   make build
   ```
   The command will do the following:

   - Install Python if you don't have it
   - Create a virtual environment (venv) in your local directory
   - Activate the virtual environment
   - Build the Docker containers and make them ready to run

- Now you have two paths:

   1- Writing your tests and run them locally using the command ```pytest```
   
   2- Writing your tests and run them inside the docker using the command ```make test```

## Contributing

Pull requests are welcome. 

For major changes, please open an issue first to discuss what you would like to change.


---
