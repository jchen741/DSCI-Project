from flask import Flask, flash, redirect, render_template, request
import firebase_admin
from firebase_admin import credentials, db
from CRUD import lookup_player_by_id, lookup_player_by_name, lookup_roster_by_team_id, find_team_id_by_name, get_roster_by_team_name,generate_player_id, add_player, update_player_info, update_team_info, delete_player

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK with credentials and database URLs
cred1 = credentials.Certificate("project-teams-1eaf5-firebase-adminsdk-gnyy9-c82edcd801.json")
cred2 = credentials.Certificate("dsci-project-2023-1-firebase-adminsdk-r980t-df15f350f1.json")
cred3 = credentials.Certificate("dsci-project-2023-2-firebase-adminsdk-4rxcr-0dd6e57f78.json")
cred4 = credentials.Certificate("dsci-project-2023-3-firebase-adminsdk-jetk4-38c745bed3.json")

# Initialize Firebase Admin SDK with credentials and database URLs
firebase_admin.initialize_app(cred1, name='app1', options={
    'databaseURL': 'https://project-teams-1eaf5-default-rtdb.firebaseio.com/'  # Link to the first database
})

firebase_admin.initialize_app(cred2, name='app2', options={
    'databaseURL': 'https://dsci-project-2023-1-default-rtdb.firebaseio.com/'  # Link to the second database
})

firebase_admin.initialize_app(cred3, name='app3', options={
    'databaseURL': 'https://dsci-project-2023-2-default-rtdb.firebaseio.com/'  # Link to the third database
})

firebase_admin.initialize_app(cred4, name='app4', options={
    'databaseURL': 'https://dsci-project-2023-3-default-rtdb.firebaseio.com/'  # Link to the fourth database
})

# Define routes
@app.route('/')
def index():
    return render_template('index.html')


# Add a route to display the search form
@app.route('/search', methods=['GET'])
def search_form():
    return render_template('search.html')

# Add routes for each option to lead to respective pages
@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        # Implement search functionality here
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        team = request.form.get('team')
        if team:
            players = get_roster_by_team_name(team)
        elif firstName or lastName:
            players = lookup_player_by_name(firstName, lastName)
        else:
            players = []
        print(players)
        return render_template('search_result.html', search_results=players)

@app.route('/update_player', methods=['GET', 'POST'])
def update_player():
    if request.method == 'POST':
        player_id = request.form.get('player_id')
        updates = {
            'firstName': request.form.get('firstName'),
            'lastName': request.form.get('lastName'),
            'birth_date': request.form.get('birth_date'),
            'height_meters': request.form.get('height_meters'),
            'jersey_num': request.form.get('jersey_num'),
            'nba_start_year': request.form.get('nba_start_year'),
            'position': request.form.get('position'),
            'team': int(request.form.get('team')),
            'weight_kg': request.form.get('weight_kg')
        }
        message = update_player_info(player_id, updates)
        return redirect('/search')
        # Receive data from the form submitted in update_player.html
        # Retrieve player data from the database using player_id
        # Implement update player functionality here, modifying the player's data
        # Redirect back to the search page after updating the player
    else:
        # Render the update_player template if the request method is GET
        player_id = request.args.get('player_id', '')
        player_data = lookup_player_by_id(player_id) if player_id else None
        return render_template('update_player.html', player = player_data)

@app.route('/update_team', methods=['GET', 'POST'])
def update_team():
    if request.method == 'POST':
        # Implement update team functionality here
        team_id = request.form.get('team_id')
        updates = {
            'name': request.form.get('name'),
            'city': request.form.get('city'),
            'code': request.form.get('code'),
            'nickname': request.form.get('nickname'),
            'logo_link': request.form.get('logo_link')
        }
        message = update_team_info(team_id, updates)
        return redirect('/search')
    else:
        return render_template('update_team.html')

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        player_info = {
            'firstName': request.form.get('firstName'),
            'lastName': request.form.get('lastName'),
            'birthdate': request.form.get('birthdate'),
            'height': request.form.get('height'),
            'nba_start_year': request.form.get('nba_start_year'),
            'position': request.form.get('position'),
            'team_id': int(request.form.get('team_id')),
            'weight': request.form.get('weight')
        }
        result = add_player(player_info)
        if result['success']:
            return redirect('/search')  # Redirect to search to see all players including the new one
        else:
            return render_template('add_player.html', error=result['Error adding player. Try again.'])
    return render_template('add_player.html')

@app.route('/delete_item', methods=['POST'])
def delete_item():
    firstName = request.form.get('firstName')
    lastName = request.form.get('lastName')
    if not firstName or not lastName:
        flash("Both first name and last name must be provided.", "error")
        return redirect('/delete_player_form')  # Assume this route shows the form

    result = delete_player(firstName, lastName)

    if result['success']:
        flash(f"Deletion successful. Players deleted: {len(result['results'])}", "success")
    else:
        # Use a default error message if 'message' key is not found
        error_message = result.get('message', 'Error deleting player.')
        flash(error_message, "error")

        # Example: db.delete_item(item_id)
        # After deletion, you may redirect to the search results or any other page
    return redirect('/search')  # Redirect back to the search results page after deletion

if __name__ == '__main__':
    app.run(debug=True)
