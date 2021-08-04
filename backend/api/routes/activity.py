from flask import Blueprint

def create_blueprint(Activity):
    blueprint = Blueprint("activity", __name__)
    
    @blueprint.route('/<pid>/<category>/<action>')
    def activity(pid, category, action):
        Activity.insert(
            pid=pid,
            category=category,
            action=action
        ).execute()

        return {"message": "activity logged"}

        
    return blueprint
