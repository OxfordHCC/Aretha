from flask import Blueprint

def create_blueprint(Activity):
    blueprint = Blueprint("activity", __name__)
    
    @blueprint.route('/<pid>/<category>/<description>', methods=['POST'])
    def post_activity(pid, category, description):
        (Activity
         .insert(pid=pid, category=category, description=description)
         .execute())

        return {"message": "activity logged"}

        
    return blueprint
