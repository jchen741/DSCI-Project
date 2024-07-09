import json
import requests
from firebase_admin import db

PLAYER_URLS = {
    0: "https://dsci-project-2023-1-default-rtdb.firebaseio.com/",
    1: "https://dsci-project-2023-2-default-rtdb.firebaseio.com/",
    2: "https://dsci-project-2023-3-default-rtdb.firebaseio.com/"
}
TEAM_URL = {
    0: "https://project-teams-1eaf5-default-rtdb.firebaseio.com/"
}

def lookup_player_by_id(player_id):
    # check each database for player_id
    for id, url in PLAYER_URLS.items():
        response = requests.get(f"{url}{player_id}.json")
        if response.status_code == 200:
            player_data = response.json()
            print(player_data)
            if player_data:
                return player_data
    return None # if not player_id exists
def lookup_player_by_name(first_name=None, last_name=None):
    players_found = []
    for db_id, url in PLAYER_URLS.items():
        if first_name and last_name:
            query_url = f"{url}.json?orderBy=\"lastname\"&equalTo=\"{last_name}\""
        elif last_name:
            query_url = f"{url}.json?orderBy=\"lastname\"&equalTo=\"{last_name}\""
        elif first_name:
            query_url = f"{url}.json?orderBy=\"firstname\"&equalTo=\"{first_name}\""
        else:
            return None  # no valid search criteria provided
        response = requests.get(query_url)
        if response.status_code == 200:
            players = response.json()
            if players:
                for key, player in players.items():
                    # if both names are provided, check the first name as well
                    if first_name and last_name:
                        if player.get('firstname', '') == first_name:
                            players_found.append(player)
                    elif last_name:
                        players_found.append(player)
                    elif first_name:
                        players_found.append(player)
    return players_found if players_found else None

def lookup_roster_by_team_id(team_id):
    db_id = team_id % 3  # hashing team_id to determine the player database
    url = PLAYER_URLS[db_id]
    query_url = f"{url}.json?orderBy=\"team\"&equalTo={team_id}"
    response = requests.get(query_url)
    if response.status_code == 200:
        roster = response.json()
        return roster if roster else None
    return None
def find_team_id_by_name(team_name):
    url = TEAM_URL[0] + ".json?orderBy=\"name\"&equalTo=\"{}\"".format(team_name)
    response = requests.get(url)
    if response.status_code == 200 and response.json() is not None:
        team_data = response.json()
        # Firebase returns a dictionary where the keys are the IDs and the values are the team data
        for team_id, data in team_data.items():
            if data['name'] == team_name:
                return team_id
    return None
def get_roster_by_team_name(team_name):
    team_id = find_team_id_by_name(team_name)
    if team_id:
        return lookup_roster_by_team_id(team_id)
    else:
        return {"success": False, "message": "Team not found."}

# need unique id
def generate_player_id():
    ref = db.reference('players')
    new_player_ref = ref.push()  # creates new key
    return new_player_ref.key
def is_player_id_unique(player_id):
    for db_id, url in PLAYER_URLS.items():
        response = requests.get(f"{url}{player_id}.json")
        if response.status_code == 200 and response.json() is not None:
            return False  # ID already exists
    return True

def add_player(player_info):
    required_fields = ['firstName', 'lastName', 'birth_date', 'height_meters', 'jersey_num','nba_start_year', 'position', 'team', 'weight_kg']
    missing_fields = [field for field in required_fields if field not in player_info or not player_info[field]]

    # check for missing fields
    if missing_fields:
        return {"success": False, "message": f"Missing required fields: {', '.join(missing_fields)}"}

    # validate team ID
    if 'team_id' not in player_info or not (0 < player_info['team_id'] <= 60):
        return {"success": False, "message": "Invalid team ID"}

    db_id = player_info['team_id'] % 3
    url = PLAYER_URLS[db_id]
    player_id = generate_player_id()
    while not is_player_id_unique(player_id):
        player_id = generate_player_id()  # regenerate ID until a unique one is found

    # convert data to JSON and put in database
    response = requests.put(f"{url}{player_id}.json", data=json.dumps(player_info))
    if response.status_code == 200:
        return {"success": True, "message": "Player added successfully", "player_id": player_id}
    else:
        return {"success": False, "message": "Failed to add player to database"}

def update_player_info(player_id, updates):
    # retrieve the player to determine the current database
    player_current_info = lookup_player_by_id(player_id)
    if not player_current_info:
        return "Player not found."

    # if 'team_id' in updates, calculate the new database; else use the current database
    if 'team_id' in updates:
        new_db_id = updates['team_id'] % 3
        current_db_id = player_current_info['team_id'] % 3
    else:
        new_db_id = current_db_id = player_current_info['team_id'] % 3

    # update player data in the new or same database
    url = PLAYER_URLS[new_db_id]
    if new_db_id != current_db_id:
        # if changing databases, remove from old and add to new
        delete_response = requests.delete(f"{PLAYER_URLS[current_db_id]}{player_id}.json")
        if delete_response.status_code != 200:
            return "Failed to remove player from old database."

    # put the updated data in the new database
    put_response = requests.put(f"{url}{player_id}.json", data=json.dumps(updates))
    return "Update successful." if put_response.status_code == 200 else "Update failed."

def update_team_info(team_id, updates):
    url = TEAM_URL[0]
    response = requests.patch(f"{url}{team_id}.json", data=json.dumps(updates))
    return "Update successful." if response.status_code == 200 else "Update failed."

def delete_player(first_name=None, last_name=None):
    # retrieve all players that match the name criteria
    players_to_delete = lookup_player_by_name(first_name, last_name)

    if not players_to_delete:
        return {"success": False, "message": "No player found with the given name."}

    deletion_results = []
    for player in players_to_delete:
        player_id = player['id']
        db_id = player['team_id'] % 3
        url = PLAYER_URLS[db_id]

        # perform the deletion
        response = requests.delete(f"{url}{player_id}.json")
        if response.status_code == 200:
            deletion_results.append({"player_id": player_id, "status": "deleted"})
        else:
            deletion_results.append({"player_id": player_id, "status": "error"})

    return {"success": True, "results": deletion_results}
