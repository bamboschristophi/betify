from flask import Flask, render_template,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

def sqlite_to_dict(sql_statement, database_name):
    import sqlite3
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    cursor.execute(sql_statement)
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    result = [dict(zip(columns, row)) for row in rows]
    connection.close()
    return result

@app.route('/deleteselection', methods=['POST'])
def deleteselection():
    ...
    return (request.form['projectFilePath'])


@app.route('/')
def home():    

    teamtodel = request.form.get('hometeamtodel')
    print (teamtodel)

    # get league (l) url parameter and pass to league Table query (n games)
    l = request.args.get('l')
    if l:
        sql = 'select * from v_leagues where League = "' + l + '" order by PTS desc, GD desc, F desc'
        leagues=sqlite_to_dict(sql, 'database.db')
    else:
        leagues = ''
        
    # get league (l) url parameter and pass to league Table query (season)    
    if l:
        sql = 'select * from v_leagues_season where League = "' + l + '" order by PTS desc, GD desc, F desc'
        leaguesseason=sqlite_to_dict(sql, 'database.db')
    else:
        leaguesseason = ''

    # get HOME team url parameter and pass to query to get last 6 results and overall stats for team
    ht = request.args.get('ht')
    if ht:
        # get home results last 6 games
        sql = 'select * from t_results where Team = "' + ht + '" order by Date desc limit 8'
        homeresults=sqlite_to_dict(sql, 'database.db')
        sql = 'select * from v_leagues where Team = "' + ht + '"'
        homeleagues = sqlite_to_dict(sql, 'database.db')
    else:
        homeresults = ''
        homeleagues = ''

    # get AWAY team url parameter and pass to query to get last n results and overall stats for team
    at = request.args.get('at')
    if at:
        # get away results last n games
        sql = 'select * from t_results where Team = "' + at + '" order by Date desc limit 8'
        awayresults=sqlite_to_dict(sql, 'database.db')
        sql = 'select * from v_leagues where Team = "' + at + '"'
        awayleagues = sqlite_to_dict(sql, 'database.db')
    else:
        awayresults = ''
        awayleagues = ''

    # get distinct leagues in fixtures for dropdown
    sql = 'select distinct League from v_fixtures'
    fixtureleagues = sqlite_to_dict(sql, 'database.db')

    # get distinct dates in fixtures for dropdown
    sql = "select distinct Match_Date from v_fixtures"
    fixturedates = sqlite_to_dict(sql, 'database.db')

    # create sql append code for fixtures sortby dropdown
    sortby = request.args.get('sortby')
    if sortby:
        if sortby == 'Rank_Diff':
            sqlsortbyappend = ' order by Rank_Diff desc'
        elif sortby == 'Match_Date':
            sqlsortbyappend = ' order by Match_Date, Kick_Off '
        else:
            sqlsortbyappend = ' order by ' + sortby
    else:
        sqlsortbyappend = 'order by Match_Date, Kick_Off '
        # set sortby to Match_Date as default
        sortby = 'Match_Date'

    # get relevant fixtures. Apply filters and sorts
    sql = 'select * from v_fixtures where 1=1 '

    # get current selections
    # sql = 'select * from t_selections where 1=1'

    # get league filter
    fl = request.args.get('fl')
    if fl == 'All' or fl == None:
        fl = 'All'
        sqlwhereleagueappend = ' '
    else:
        sqlwhereleagueappend = 'and League = "' + fl + '" '

    # get date filter
    fd = request.args.get('fd')
    if fd == 'All' or fd == None:
        fd = 'All'
        sqlwheredateappend = ' '
    else:
        sqlwheredateappend = 'and Match_Date = "' + fd + '" '

    # join sql statement sections together and execute
    sql = sql + sqlwhereleagueappend + sqlwheredateappend + sqlsortbyappend
    fixtures=sqlite_to_dict(sql, 'database.db')

    # get all selections
    # sql = 'select * from t_selections'
    # selections=sqlite_to_dict(sql, 'database.db')    

    return render_template('home.html',  
                           fixtures=fixtures, 
                           leagues=leagues, 
                           leaguesseason=leaguesseason,
                           l=l, 
                           homeresults = homeresults, 
                           awayresults=awayresults, 
                           ht=ht, 
                           at=at, 
                           awayleagues=awayleagues, 
                           homeleagues=homeleagues,
                           fixtureleagues=fixtureleagues,
                           fixturedates=fixturedates,
                           fl=fl,
                           fd=fd,
                           sortby=sortby,
                        #    selections=selections
                           )

if __name__ == '__main__':
    app.run(debug=True)