from flask import Flask,g,request,jsonify
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from database_helpers import get_db
from functools import wraps
load_dotenv()
api_username=os.getenv('API_USERNAME')
api_password=os.getenv('API_PASSWORD')

app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.client.close()
#define decorator for authorization named protected
#@wraps(f) is a decorator from the functools module that preserves the original function’s
# information (like its name and docstring),
#which is useful for debugging and introspection.
def protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth=request.authorization
        if auth and auth.username==api_username and auth.password==api_password:
            return f(*args, **kwargs)
        return jsonify({'error':'Invalid username or password, No Authorization'}), 403    
    return decorated



@app.route('/member')
@protected
def get_all_members():
    db=get_db()
    members_collection=db.members
    
    members=members_collection.find()
    
    members_list=[]
    
    for member in members:
        members_list.append({
            '_id': str(member['_id']),
            'name': member['name'],
            'age': member['age'],
            'email': member['email'],
            'level': member['level']
        })

    return jsonify({'members':members_list})

@app.route('/member/<member_id>')
@protected
def get_member(member_id):
    db=get_db()
    members_collection=db.members
    
    member=members_collection.find_one({'_id': ObjectId(member_id)})
    
    return jsonify({'member':{
        '_id': str(member['_id']),
        'name': member['name'],
        'age': member['age'],
        'email': member['email'],
        'level': member['level']
    }})

@app.route('/member',methods=['POST'])
@protected
def add_member():
    db=get_db()
    members_collection=db.members
    
    member_json=request.get_json()
    
    member=members_collection.insert_one({
        'name': member_json['name'],
        'age': member_json['age'],
        'email': member_json['email'],
        'level': member_json['level'],
    })
    
    member_added=members_collection.find_one({'name': member_json['name']})
    return jsonify({
        '_id': str(member_added['_id']),
        'name': member_added['name'],
        'age': member_added['age'],
        'email': member_added['email'],
        'level': member_added['level']
    })

@app.route('/member/<member_id>',methods=['PUT','PATCH'])
@protected
def edit_member(member_id):
    db=get_db()
    members_collection=db.members
    member_json = request.get_json()  

    # Build the update operation
    update_fields = {}
    for key in ['name', 'age', 'email', 'level']:
        if key in member_json:
            update_fields[key] = member_json[key]
    print(update_fields)

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    # Perform the update
    result = members_collection.update_one(
        {'_id': ObjectId(member_id)},
        {'$set': update_fields}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Member not found"}), 404

    # Return the updated document
    member_updated = members_collection.find_one({'_id': ObjectId(member_id)})
    return jsonify({'member_updated':{
        '_id': str(member_updated['_id']),
        'name': member_updated['name'],
        'age': member_updated['age'],
        'email': member_updated['email'],
        'level': member_updated['level']
    }})

@app.route('/member/<member_id>',methods=['DELETE'])
@protected
def delete_member(member_id):
    db=get_db()
    members_collection=db.members
    
    member=members_collection.delete_one({'_id':ObjectId(member_id)})
    
    
    return jsonify({'message':f'Member deleted successfully: {member.acknowledged}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)