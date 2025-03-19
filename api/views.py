import jwt
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from pymongo import MongoClient
from django.conf import settings
import re
from bson.objectid import ObjectId
from django.views.decorators.csrf import csrf_exempt
import certifi
import datetime


# ✅ Get MongoDB URI from settings.py
MONGO_URI = getattr(settings, "MONGO_URI", "mongodb+srv://tayyab:angel123@cluster0.x7zaa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ✅ Secure connection to MongoDB Atlas
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["workshop"]  # Change this to your database name

# ✅ Collections
users_collection = db["users"]
tasks_collection = db["tasks"]
parts_collection = db["vehicle_parts"]

# ✅ Signup View
@csrf_exempt
def signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extract user details
            full_name = data.get("full_name")
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            dob = data.get("dob")
            present_address = data.get("present_address")
            permanent_address = data.get("permanent_address")
            city = data.get("city")
            postal_code = data.get("postal_code")
            country = data.get("country")
            role = data.get("role", "user").lower()  # Default role is "user"

            # ✅ Validate required fields
            required_fields = ["full_name", "username", "email", "password", "dob", "present_address", "permanent_address", "city", "postal_code", "country"]
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({"error": f"{field.replace('_', ' ').title()} is required"}, status=400)

            # ✅ Validate role field
            valid_roles = ["user", "admin", "owner"]
            if role not in valid_roles:
                return JsonResponse({"error": "Invalid role. Must be 'user', 'admin', or 'owner'"}, status=400)

            # ✅ Validate email format
            email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_regex, email):
                return JsonResponse({"error": "Invalid email format"}, status=400)

            # ✅ Validate username uniqueness
            if users_collection.find_one({"username": username}):
                return JsonResponse({"error": "Username already exists"}, status=400)

            # ✅ Validate email uniqueness
            if users_collection.find_one({"email": email}):
                return JsonResponse({"error": "Email already registered"}, status=400)

            # ✅ Validate password security
            if len(password) < 8:
                return JsonResponse({"error": "Password must be at least 8 characters long"}, status=400)
            if not any(char.isdigit() for char in password):
                return JsonResponse({"error": "Password must contain at least one number"}, status=400)
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                return JsonResponse({"error": "Password must contain at least one special character"}, status=400)

            # ✅ Insert user into MongoDB (without password hashing)
            user = {
                "full_name": full_name,
                "username": username,
                "email": email,
                "password": password,  # ⚠️ No hashing applied
                "dob": dob,
                "present_address": present_address,
                "permanent_address": permanent_address,
                "city": city,
                "postal_code": postal_code,
                "permanent_address": permanent_address,
                "country": country,
                "role": role  # ✅ Adding role field
            }
            users_collection.insert_one(user)

            return JsonResponse({"message": "User registered successfully!", "role": role}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


SECRET_KEY = "your_secret_key_here"  # Replace with a secure secret key

@csrf_exempt
def signin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            email = data.get("email")
            password = data.get("password")

            # ✅ Validate input
            if not email or not password:
                return JsonResponse({"error": "Email and password are required"}, status=400)

            # ✅ Find user in the database
            user = users_collection.find_one({"email": email})

            if not user:
                return JsonResponse({"error": "User not found"}, status=400)

            # ✅ Check if password matches
            if user["password"] != password:
                return JsonResponse({"error": "Incorrect password"}, status=400)

            # ✅ Generate JWT token
            payload = {
                "username": user["username"],
                "email": user["email"],
                "role":user["role"],
                "dob":user["dob"],
                "city":user["city"],
                "present_address":user["present_address"],
                "postal_code":user["postal_code"],
                "userId":str(user["_id"]),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)  # Token expires in 2 hours
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return JsonResponse({
                "message": "Login successful!",
                # "user": {
                #     "full_name": user["full_name"],
                #     "email": user["email"],
                #     "username": user["username"]
                # },
                "token": token,
                
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


## delete user
@csrf_exempt
def delete_user(request, user_id):
    if request.method == "DELETE":
        try:
            # ✅ Check if user_id is a valid ObjectId
            if not ObjectId.is_valid(user_id):
                return JsonResponse({"error": "Invalid user ID format"}, status=400)

            # ✅ Find and delete the user from the database
            result = users_collection.delete_one({"_id": ObjectId(user_id)})

            if result.deleted_count == 0:
                return JsonResponse({"message": "User not found"}, status=404)

            return JsonResponse({"message": "User deleted successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)



# ✅ Fetch User Info
def get_user(request, email):
    user = users_collection.find_one({"email": email}, {"_id": 0})  # Exclude MongoDB `_id`
    if user:
        return JsonResponse(user, status=200)
    return JsonResponse({"error": "User not found"}, status=404)

# ✅ Update User Info
@csrf_exempt
def update_user(request, email):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)

            # Ensure user exists
            user = users_collection.find_one({"email": email})
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)

            # ✅ Update user information
            users_collection.update_one({"email": email}, {"$set": data})
            return JsonResponse({"message": "User updated successfully!"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# fetch the users
def get_all_users(request):
    if request.method == "GET":
        try:
            users = list(users_collection.find({}))  # Fetch all users
            
            # Convert `_id` (ObjectId) to string and bytes fields to string
            for user in users:
                user["_id"] = str(user["_id"])  # Convert ObjectId to string
                
                # Convert any bytes fields to string
                for key, value in user.items():
                    if isinstance(value, bytes):
                        user[key] = value.decode("utf-8")  # Decode bytes to string
            
            return JsonResponse(users, safe=False) if users else JsonResponse({"message": "No users found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)


# @csrf_exempt
# def create_task(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)

#             # Extract task details
#             vehicle_name = data.get("vehicle_name")
#             vehicle_number = data.get("vehicle_number")
#             customer_name = data.get("customer_name")
#             check_in_time = data.get("check_in_time")
#             task_description = data.get("task_description", "")  # Default to empty if not provided
#             assigned_user_id = data.get("assigned_user_id")  # User ID from MongoDB

#             # ✅ Validate required fields
#             required_fields = ["vehicle_name", "vehicle_number", "customer_name", "check_in_time", "assigned_user_id"]
#             for field in required_fields:
#                 if not data.get(field):
#                     return JsonResponse({"error": f"{field.replace('_', ' ').title()} is required"}, status=400)

#             # ✅ Convert check-in time to datetime format
#             try:
#                 check_in_time = datetime.strptime(check_in_time, "%Y-%m-%dT%H:%M:%S")
#             except ValueError:
#                 return JsonResponse({"error": "Invalid check-in time format. Use YYYY-MM-DDTHH:MM:SS"}, status=400)

#             # ✅ Check if assigned_user_id is a valid ObjectId
#             if not ObjectId.is_valid(assigned_user_id):
#                 return JsonResponse({"error": "Invalid user ID format"}, status=400)

#             # ✅ Find assigned user in MongoDB
#             assigned_user = users_collection.find_one({"_id": ObjectId(assigned_user_id)}, {"_id": 1, "username": 1, "email": 1})
#             if not assigned_user:
#                 return JsonResponse({"error": "User not found"}, status=400)

#             # ✅ Create task document
#             task = {
#                 "vehicle_name": vehicle_name,
#                 "vehicle_number": vehicle_number,
#                 "customer_name": customer_name,
#                 "check_in_time": check_in_time,
#                 "task_description": task_description,
#                 "task_status": "pending",  # Default task status
#                 "assigned_user_id": assigned_user["_id"]  # Store user ID
#             }

#             # ✅ Insert into MongoDB
#             result = tasks_collection.insert_one(task)

#             return JsonResponse({
#                 "message": "Task created successfully!",
#                 "task_id": str(result.inserted_id),
#                 "task_status": "pending",
#                 "assigned_user": {
#                     "user_id": str(assigned_user["_id"]),
#                     "username": assigned_user["username"],
#                     "email": assigned_user["email"]
#                 }
#             }, status=201)

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON"}, status=400)

#     return JsonResponse({"error": "Method not allowed"}, status=405)




## with parts functon
# @csrf_exempt
# def create_task(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)

#             # Extract task details
#             vehicle_name = data.get("vehicle_name")
#             vehicle_number = data.get("vehicle_number")
#             customer_name = data.get("customer_name")
#             check_in_time = data.get("check_in_time")
#             task_description = data.get("task_description", "")
#             assigned_user_id = data.get("assigned_user_id")

#             # ✅ Validate required fields
#             required_fields = ["vehicle_name", "vehicle_number", "customer_name", "check_in_time", "assigned_user_id"]
#             for field in required_fields:
#                 if not data.get(field):
#                     return JsonResponse({"error": f"{field.replace('_', ' ').title()} is required"}, status=400)

#             # ✅ Convert check-in time to datetime format
#             try:
#                 check_in_time = datetime.strptime(check_in_time, "%Y-%m-%dT%H:%M:%S")
#             except ValueError:
#                 return JsonResponse({"error": "Invalid check-in time format. Use YYYY-MM-DDTHH:MM:SS"}, status=400)

#             # ✅ Check if assigned_user_id is a valid ObjectId
#             if not ObjectId.is_valid(assigned_user_id):
#                 return JsonResponse({"error": "Invalid user ID format"}, status=400)

#             # ✅ Find assigned user in MongoDB
#             assigned_user = users_collection.find_one({"_id": ObjectId(assigned_user_id)}, {"_id": 1, "username": 1, "email": 1})
#             if not assigned_user:
#                 return JsonResponse({"error": "User not found"}, status=400)

#             # ✅ Create task document with an empty "parts" array
#             task = {
#                 "vehicle_name": vehicle_name,
#                 "vehicle_number": vehicle_number,
#                 "customer_name": customer_name,
#                 "check_in_time": check_in_time,
#                 "task_description": task_description,
#                 "task_status": "pending",
#                 "assigned_user_id": assigned_user["_id"],
#                 "parts": []  # ✅ New field for storing parts
#             }

#             # ✅ Insert into MongoDB
#             result = tasks_collection.insert_one(task)

#             return JsonResponse({
#                 "message": "Task created successfully!",
#                 "task_id": str(result.inserted_id),
#                 "task_status": "pending",
#                 "assigned_user": {
#                     "user_id": str(assigned_user["_id"]),
#                     "username": assigned_user["username"],
#                     "email": assigned_user["email"]
#                 },
#                 "parts": []
#             }, status=201)

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON"}, status=400)

#     return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def create_task(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extract task details
            vehicle_name = data.get("vehicle_name")
            vehicle_number = data.get("vehicle_number")
            customer_name = data.get("customer_name")
            check_in_time = data.get("check_in_time")
            task_description = data.get("task_description", "")
            assigned_user_id = data.get("assigned_user_id")

            # Validate required fields
            required_fields = ["vehicle_name", "vehicle_number", "customer_name", "check_in_time", "assigned_user_id"]
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({"error": f"{field.replace('_', ' ').title()} is required"}, status=400)

            # Convert check-in time to datetime format
            try:
                check_in_time = datetime.strptime(check_in_time, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return JsonResponse({"error": "Invalid check-in time format. Use YYYY-MM-DDTHH:MM:SS"}, status=400)

            # Check if assigned_user_id is a valid ObjectId
            if not ObjectId.is_valid(assigned_user_id):
                return JsonResponse({"error": "Invalid user ID format"}, status=400)

            # Find assigned user in MongoDB
            assigned_user = users_collection.find_one({"_id": ObjectId(assigned_user_id)}, {"_id": 1, "username": 1, "email": 1})
            if not assigned_user:
                return JsonResponse({"error": "User not found"}, status=400)

            # Create task document with an empty 'task_parts' array
            task = {
                "vehicle_name": vehicle_name,
                "vehicle_number": vehicle_number,
                "customer_name": customer_name,
                "check_in_time": check_in_time,
                "task_description": task_description,
                "task_status": "pending",
                "assigned_user_id": assigned_user["_id"],
                "task_parts": []  # Empty array for parts initially
            }

            # Insert into MongoDB
            result = tasks_collection.insert_one(task)

            return JsonResponse({
                "message": "Task created successfully!",
                "task_id": str(result.inserted_id),
                "task_status": "pending",
                "assigned_user": {
                    "user_id": str(assigned_user["_id"]),
                    "username": assigned_user["username"],
                    "email": assigned_user["email"]
                },
                "task_parts": []
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# add task new chat function
@csrf_exempt
def add_task_part(request, task_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            part_id = data.get("part_id")

            # Validate part_id
            if not part_id or not ObjectId.is_valid(part_id):
                return JsonResponse({"error": "Invalid part ID format"}, status=400)

            # Validate task_id
            if not ObjectId.is_valid(task_id):
                return JsonResponse({"error": "Invalid task ID format"}, status=400)

            # Find the task in MongoDB
            task = tasks_collection.find_one({"_id": ObjectId(task_id)})
            if not task:
                return JsonResponse({"error": "Task not found"}, status=404)

            # Find the part in the correct collection (vehicle_parts)
            part = db["vehicle_parts"].find_one({"_id": ObjectId(part_id)})
            if not part:
                return JsonResponse({"error": "Part not found"}, status=404)

            # Debugging: Print retrieved part to verify
            print("Part found:", part)

            # Update task document by adding the part
            tasks_collection.update_one(
                {"_id": ObjectId(task_id)},
                {"$push": {"task_parts": {
                    "part_id": str(part["_id"]),
                    "part_name": part.get("part_name", "Unknown"),
                    "part_price": part.get("price",0),
                    "company_name":part.get("company_name","Unknown"),
                    "stock_quantity":part.get("stock_quantity",0),
                    "vehicle_model":part.get("vehicle_model",0),
                    "part_number":part.get("part_number",0),
                    "added_on":part.get("added_on",0)
                }}}
            )

            return JsonResponse({
                "message": "Part added successfully!",
                "task_id": task_id,
                "added_part": {
                    "part_id": str(part["_id"]),
                    "part_name": part.get("part_name", "Unknown"),
                    "part_price": part.get("part_price", 0)
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

# get task wiith parts
@csrf_exempt
def get_user_tasks_with_parts(request, user_id):
    if request.method == "GET":
        try:
            # Validate user_id
            if not ObjectId.is_valid(user_id):
                return JsonResponse({"error": "Invalid user ID format"}, status=400)

            # Find the user in MongoDB
            user = users_collection.find_one({"_id": ObjectId(user_id)}, {"_id": 1, "username": 1, "email": 1})
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)

            # Find tasks assigned to the user
            tasks = list(tasks_collection.find({"assigned_user_id": ObjectId(user_id)}))

            # If no tasks are found, return an empty list
            if not tasks:
                return JsonResponse({"message": "No tasks found for this user", "tasks": []}, status=200)

            # Format task data
            formatted_tasks = []
            for task in tasks:
                formatted_tasks.append({
                    "task_id": str(task["_id"]),
                    "vehicle_name": task.get("vehicle_name"),
                    "vehicle_number": task.get("vehicle_number"),
                    "customer_name": task.get("customer_name"),
                    "check_in_time": task.get("check_in_time").strftime("%Y-%m-%d %H:%M:%S"),
                    "task_description": task.get("task_description", ""),
                    "task_status": task.get("task_status", "pending"),
                    "task_parts": task.get("task_parts", []),  # List of parts
                })

            # Return response
            return JsonResponse({
                "user": {
                    "user_id": str(user["_id"]),
                    "username": user["username"],
                    "email": user["email"]
                },
                "tasks": formatted_tasks
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# get task with task id



## edit the task
@csrf_exempt
def update_task(request, task_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)

            # ✅ Check if task_id is a valid ObjectId
            if not ObjectId.is_valid(task_id):
                return JsonResponse({"error": "Invalid task ID format"}, status=400)

            # ✅ Find the existing task
            task = tasks_collection.find_one({"_id": ObjectId(task_id)})
            if not task:
                return JsonResponse({"error": "Task not found"}, status=404)

            # ✅ Extract updated fields (only update provided fields)
            update_fields = {}
            if "vehicle_name" in data:
                update_fields["vehicle_name"] = data["vehicle_name"]
            if "vehicle_number" in data:
                update_fields["vehicle_number"] = data["vehicle_number"]
            if "customer_name" in data:
                update_fields["customer_name"] = data["customer_name"]
            if "task_description" in data:
                update_fields["task_description"] = data["task_description"]
            if "task_status" in data:
                update_fields["task_status"] = data["task_status"]

            # ✅ Handle check-in time update if provided
            if "check_in_time" in data:
                try:
                    update_fields["check_in_time"] = datetime.strptime(data["check_in_time"], "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return JsonResponse({"error": "Invalid check-in time format. Use YYYY-MM-DDTHH:MM:SS"}, status=400)

            # ✅ Handle assigned user update if provided
            if "assigned_user_id" in data:
                if not ObjectId.is_valid(data["assigned_user_id"]):
                    return JsonResponse({"error": "Invalid user ID format"}, status=400)

                assigned_user = users_collection.find_one({"_id": ObjectId(data["assigned_user_id"])}, {"_id": 1})
                if not assigned_user:
                    return JsonResponse({"error": "Assigned user not found"}, status=400)

                update_fields["assigned_user_id"] = assigned_user["_id"]

            # ✅ Update the task in MongoDB
            tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": update_fields})

            return JsonResponse({"message": "Task updated successfully"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

## update task status
@csrf_exempt
def update_task_status(request, task_id):
    if request.method == "PATCH":  # PATCH is used for partial updates
        try:
            data = json.loads(request.body)

            # ✅ Validate task_id
            if not ObjectId.is_valid(task_id):
                return JsonResponse({"error": "Invalid task ID format"}, status=400)

            # ✅ Validate status field
            new_status = data.get("task_status")
            if not new_status:
                return JsonResponse({"error": "Task status is required"}, status=400)

            # ✅ Find the task in MongoDB
            task = tasks_collection.find_one({"_id": ObjectId(task_id)})
            if not task:
                return JsonResponse({"error": "Task not found"}, status=404)

            # ✅ Update the task status
            tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"task_status": new_status}})

            return JsonResponse({"message": "Task status updated successfully", "task_status": new_status}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

## task fetch for the specific user
from bson import ObjectId

def get_tasks_by_user(request, user_id):
    if request.method == "GET":
        try:
            # Convert user_id to ObjectId
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                return JsonResponse({"error": "Invalid user ID format"}, status=400)

            # Query tasks assigned to this user
            tasks = list(tasks_collection.find({"assigned_user_id": user_obj_id}))

            if not tasks:
                return JsonResponse({"message": "No tasks found for this user"}, status=404)

            # Convert ObjectId fields to string for JSON response
            for task in tasks:
                task["_id"] = str(task["_id"])
                task["assigned_user_id"] = str(task["assigned_user_id"])  # Convert assigned user ID to string

            return JsonResponse(tasks, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


## fetch the single task by using the id of task
def get_task_by_id(request, task_id):
    if request.method == "GET":
        try:
            # ✅ Check if task_id is a valid ObjectId
            if not ObjectId.is_valid(task_id):
                return JsonResponse({"error": "Invalid task ID format"}, status=400)

            # ✅ Find task in the database
            task = tasks_collection.find_one({"_id": ObjectId(task_id)})

            if not task:
                return JsonResponse({"message": "Task not found"}, status=404)

            # ✅ Convert ObjectId fields to string for JSON response
            task["_id"] = str(task["_id"])
            task["assigned_user_id"] = str(task["assigned_user_id"])

            return JsonResponse(task, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)