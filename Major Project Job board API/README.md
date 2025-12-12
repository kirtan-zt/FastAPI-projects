
# Major Project

Job board API for job seekers and recruiters, to view new job postings and apply for their desired job title

## Features

- Job Posting CRUD for recruiters
- Job Search & Filters for job seekers
- Company Profiles
- Tag-based filtering (e.g., Python, Remote, Intern)
- Profile completion criteria (bio, past experience, skills)
- Set application status to 'Accepted', 'Rejected', 'Under Review'
- Set listing status to 'Still Accepting', 'Expired'

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

It's best to install Python projects in a Virtual Environment. Once you have set up a VE, clone this project
```bash
git clone https://github.com/dave-kirtan/FastAPI-projects.git
```
```bash
pip install -r requirements.txt
```
```bash
cd FastAPI-projects/Major Project Job board API
```




## Environment Variables
The application uses an .env file to manage environment varialbes. A .env.example file is included in the project for your modification. (Remember to rename the file to .env in order for your environment variables to be read.)

The configuration can be changed to use the OS environment based on the FastAPI Settings documentation if you prefer.

```bash
alembic upgrade head
```

## Starting the application


### Note: 
You must create a postgres database the same as your env, before running alembic upgrade head.

### Running the server
Once the prerequisites are met, The following steps can be used to get the application up and running. All commands are run from the root directory of the project
```bash
uvicorn main:app --reload
```
## API Reference

#### User registration

```http
  POST /users/register
```


#### Login and access token

```http
  POST /users/login
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `email`      | `EmailStr` | **Required**. User's email
| `password`    | `str`   | **Required**. Password


#### Remove user profile

```http
  DELETE /users/me
```


# User's role is a recruiter 
```http
  POST /companies/
```

 Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `email`      | `EmailStr` | **Required**. Company's email
| `name`    | `str`   | **Required**. Name of company |
| `industry` | `enum` | **Required**. Type of Industry (e.g. IT, manufacturing) |
| `location` | `str` | **Required**. Location |
| `Description` | `str` | **Required** Company Bio |
| `Website` | `str` | **Required** website URL |

#### Fetch all companies data
```http
  GET /companies/
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `skip`      | `int` | Optional. Paginate from {value}   |
| `limit`    | `int`   | Optional. Paginate till {value} |

#### Fetch a company by id
```http
  GET /companies/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Company id  |


### Update existing company data by id
```http
 PATCH /companies/id
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Company id  |
| `email`      | `EmailStr` | Optional. Company's email
| `name`    | `str`   | Optional. Name of company |
| `industry` | `enum` | Optional. Type of Industry (e.g. IT, manufacturing) |
| `location` | `str` | Optional. Location |
| `Description` | `str` | Optional Company Bio |
| `Website` | `str` | Optional website URL |


### Delete company from Job platform
```http
 DELETE /companies/id
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Company id  |


## Once company is registered, add recruiter Bio
```http
  POST /recruiters/
```

 Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `first_name`    | `str`   | **Required**. First name |
| `last_name` | `str` | **Required**. Last name |
| `company id` | `Foreign Key` | **Required**. Company id |
| `position` | `str` | **Required** Designation of recruiter |
| `phone number` | `str` | **Required** Contact details |

### Read all recruiter details

```http
  GET /recruiters/
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `skip`      | `int` | Optional. Paginate from {value}   |
| `limit`    | `int`   | Optional. Paginate till {value} |

### Read recruiter information by id
```http
  GET /recruiters/id
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Recruiter id  |

### Update recruiter Bio by id
```http
  PATCH /recruiters/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Recruiter id  |
| `first_name`    | `str`   | Optional. First name |
| `last_name` | `str` | Optional. Last name |
| `company id` | `Foreign Key` | Optional Company id |
| `position` | `str` | Optional Designation of recruiter |
| `phone number` | `str` | Optional Contact details |

### Delete recruiter information from Job platform
```http
  DELETE /recruiters/id
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Recruiter id  | 

## Create a job listing
```http
  POST /listings/
```
 Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `company id`      | `Foreign Key` | **Required**. Company's id
| `title`    | `str`   | **Required**. Job title |
| `description` | `str` | **Required**. Job description (JD) |
| `location` | `enum` | **Required**. On-site, Remote, Hybrid |
| `salary range` | `enum` | **Required** Range of salary |
| `employment` | `enum` | **Required** Full-time, Intern |
| `application deadline` | `date` | **Required** Last day to apply |
| `is active` | `enum` | **Required** Listing is expired or still accepting |

### Read all listings
```http
  GET /listings/
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `skip`      | `int` | Optional. Paginate from {value}   |
| `limit`    | `int`   | Optional. Paginate till {value} |

### Read listings by id
```http
  GET /listings/id
  ```
  | Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Listing id  | 

### Read listings by title, location, etc. (Tag-Based)
```http
  GET /listings/search
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `title`      | `str` | Optional. Job title    |
| `location`    | `str`   | Optional. On-site, Remote |
| `employment type`    | `str`   | Optional. Full time, Part time |

### Update listing details by id
```http
  PATCH /listings/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Listing id  |
| `application_deadline`      | `date` | **Optional**.   |
| `is_active`      | `enum` | **Optional**. Expired, Still accepting  |
| `title`      | `str` | **Optional**. Job title  |
| `description`      | `str` | **Optional**. Description  |

### Delete a listing by id
```http
  DELETE /listings/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Listing id  |


# User's role a job seeker
### Add bio of job seeker
```http
  POST /seekers/
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `first_name`    | `str`   | Required. First name |
| `last_name` | `str` | Required. Last name |
| `desired_job_title` | `str` | Required Desired title |
| `phone number` | `str` | Required Contact details |
| `location` | `str` | Required Location of candidate |
| `current salary` | `str` | Required Current salary CTC |
| `past experience` | `str` | Optional past experience if any |
| `skill set` | `str` | Optional Skill set |

### Read job seekers information
```http
  GET /seekers/
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `skip`      | `int` | Optional. Paginate from {value}   |
| `limit`    | `int`   | Optional. Paginate till {value} |

### Read job seeker by id
```http
  GET /seekers/id
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Job seeker id  |

### Read job seeker's profile completion score
```http
  GET /seekers/id/completion
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Job seeker id  |

### Update job seeker details by id
```http
  PATCH /seekers/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Job seeker id  |
| `first_name`    | `str`   | Optional. First name |
| `last_name` | `str` | Optional. Last name |
| `desired_job_title` | `str` | Optional Desired title |
| `phone number` | `str` | Optional Contact details |
| `location` | `str` | Optional Location of candidate |
| `current salary` | `str` | Optional Current salary CTC |
| `past experience` | `str` | Optional past experience if any |
| `skill set` | `str` | Optional Skill set |

### Delete job seeker profile by id
```http
  DELETE /seekers/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Job seeker id  |

## Apply for a listing created by recruiter
```http
  POST /applications/
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `status`      | `enum` | **Required**. Pending, Accepted  |
| `listing id`      | `Foreign Key` | **Required**. Listing id  |
| `job seeker id`      | `Foreign Key` | **Required**. Job seeker id  |
| `applied date`      | `str` | **Required**. Date of application  |


### Fetch all applications
```http
  GET /applications/
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `skip`      | `int` | Optional. Paginate from {value}   |
| `limit`    | `int`   | Optional. Paginate till {value} |

### Fetch application by id
```http
  GET /applications/id
  ```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Application id  |

### Update application status of a listing by application id
```http
  PATCH /applications/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Application id  |
| `status`      | `enum` | **Required**. Pending, Accepted  |
| `listing id`      | `Foreign Key` | **Required**. Listing id  |
| `job seeker id`      | `Foreign Key` | **Required**. Job seeker id  |
| `applied date`      | `str` | **Required**. Date of application  |

### Delete application by id
```http
  DELETE /applications/id
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Application id  |
