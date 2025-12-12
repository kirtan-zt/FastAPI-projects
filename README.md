
# Minor Project

Recipe API is a minor project to add, update, delete recipe procedure, time required to make that recipe, etc.

## Features

- Create a new recipe with an appropriate name.
- Add the procedure, type of recipe, preparation time.
- Update the details and delete a recipe if not required. 


## Starting the application

### Running the server
```bash
uvicorn main:app --reload
```
## API Reference

#### User registration

```http
  POST /register
```

#### Login and access token

```http
  POST /token
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `email`      | `EmailStr` | **Required**. User's email
| `password`    | `str`   | **Required**. Password


#### Remove user profile

```http
  DELETE /me
```


### Add recipe 
```http
  POST /recipes/
```

 Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `recipe_name`    | `str`   | **Required**. Name of recipe |
| `recipe_choice` | `enum` | **Required**. Type of recipe (e.g. breakfast, lunch) |
| `recipe_method` | `str` | **Required**. Method to prepare dish |
| `prep_time_in_min` | `int` | **Required** Time it takes to prepare |

### Fetch all recipe information
```http
  GET /recipes/
```

### Fetch a recipe detail by id
```http
  GET /recipes/{recipe_id}
```
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `recipe_id`      | `int` | **Required**. Recipe id  |


### Update existing recipe data by id
```http
 PATCH /recipes/{recipe_id}
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Company id  |
| `recipe_name`    | `str`   | **Optional**. Name of recipe |
| `recipe_choice` | `enum` | **Optional**. Type of recipe (e.g. breakfast, lunch) |
| `recipe_method` | `str` | **Optional**. Method to prepare dish |
| `prep_time_in_min` | `int` | **Optional** Time it takes to prepare |


### Delete recipe from database
```http
 DELETE /recipes/{recipe_id}
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `int` | **Required**. Recipe id  |


