from flask import Flask, jsonify, request
from nba_api.stats.endpoints import playbyplayv2, commonteamroster, boxscoresummaryv2, teaminfocommon
import pandas as pd

app = Flask(__name__)

def find_last_scorer(game_id):
    # Fetch play-by-play data for the specified game
    play_by_play = playbyplayv2.PlayByPlayV2(game_id=game_id)
    
    # Convert the data to a DataFrame
    play_by_play_df = play_by_play.get_data_frames()[0]

    # Filter for scoring plays
    scoring_plays = play_by_play_df[play_by_play_df['EVENTMSGTYPE'] == 1]

    # Find the last scoring play
    if not scoring_plays.empty:
        last_scoring_play = scoring_plays.iloc[-1]
        scorer_id = int(last_scoring_play['PLAYER1_ID'])  # Convert to native Python int
        return scorer_id
    else:
        return None
    
def get_coaches(team_id):
    team_roster = commonteamroster.CommonTeamRoster(team_id=team_id)
    team_roster_df = team_roster.get_data_frames()[1]  # The second DataFrame contains coaches
    return team_roster_df

def get_game_teams(game_id):
    game_summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
    game_summary_df = game_summary.get_data_frames()[0]
    return game_summary_df['HOME_TEAM_ID'].iloc[0], game_summary_df['VISITOR_TEAM_ID'].iloc[0]

def get_team_details(team_id):
    team_info = teaminfocommon.TeamInfoCommon(team_id=team_id)
    team_info_df = team_info.get_data_frames()[0]
    return {
        "team_id": int(team_id),  # Convert to native Python int
        "team_name": team_info_df['TEAM_CITY'].iloc[0] + " " + team_info_df['TEAM_NAME'].iloc[0],
        "team_abbreviation": team_info_df['TEAM_ABBREVIATION'].iloc[0]
    }

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/getgameteams', methods=['GET'])
def get_game_teams_info():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({"error": "Missing game_id parameter"}), 400

    try:
        game_summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
        game_summary_df = game_summary.get_data_frames()[0]
        home_team_id = game_summary_df['HOME_TEAM_ID'].iloc[0]
        visitor_team_id = game_summary_df['VISITOR_TEAM_ID'].iloc[0]

        home_team_details = get_team_details(home_team_id)
        visitor_team_details = get_team_details(visitor_team_id)

        return jsonify({
            "home_team": home_team_details,
            "visitor_team": visitor_team_details
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/getgamecoaches', methods=['GET'])
def get_game_coaches():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({"error": "Missing game_id parameter"}), 400

    try:
        home_team_id, visitor_team_id = get_game_teams(game_id)
        home_coaches = get_coaches(home_team_id).to_dict(orient='records')
        visitor_coaches = get_coaches(visitor_team_id).to_dict(orient='records')
        return jsonify({"home_coaches": home_coaches, "visitor_coaches": visitor_coaches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/findlastscorer', methods=['GET'])
def get_last_scorer():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({"error": "Missing game_id parameter"}), 400

    try:
        last_scorer_id = find_last_scorer(game_id)
        if last_scorer_id:
            return jsonify({"last_scorer_id": last_scorer_id})
        else:
            return jsonify({"message": "No scoring plays found in the game."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
