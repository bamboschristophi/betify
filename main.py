import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from seleniumbase import Driver
from bs4 import BeautifulSoup
import datetime
import re    
from playwright.sync_api import sync_playwright

import warnings
warnings.filterwarnings('ignore')

# show all pandas columns and rows
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def get_results(league_id):
    url = f'https://www.football-data.co.uk/mmz4281/2425/{league_id}.csv'
    results = pd.read_csv(url, parse_dates=['Date'], dayfirst=True, encoding='cp1252')
    return results.iloc[:, :23].drop(columns=['Referee'], errors='ignore')

def process_results(results, games=None):

    # Process Home Data

    # copy the results dataframe to a new dataframe called results_home
    results_home = results.copy()

    # create a column called Team, after Date. Copy HomeTeam to Team
    results_home.insert(1, 'Team', results_home['HomeTeam'])
    # tirm Team column
    results_home['Team'] = results_home['Team'].str.strip()

    # add columns called Venue with Value 'Home'
    results_home.insert(2, 'Venue', 'Home')

    # change AwayTeam to Opponent
    results_home.rename(columns={'AwayTeam': 'Opponent'}, inplace=True)
    # trim Opponent column
    results_home['Opponent'] = results_home['Opponent'].str.strip()

    # drop HomeTeam column
    results_home.drop('HomeTeam', axis=1, inplace=True)

    # rename columns FTHG to GoalsFor and FTAG to GoalsAgainst
    results_home.rename(columns={'FTHG': 'Goals', 
                                'FTAG': 'GoalsOpponent', 
                                'HTHG': 'HalfTimeGoals',
                                'HTAG':'HalfTimeGoalsOpponent',
                                'HS':'Shots',
                                'AS':'ShotsOpponent',
                                'HST':'ShotsOnTarget',
                                'AST':'ShotsOnTargetOpponent',
                                'HF':'Fouls',
                                'AF':'FoulsOpponent',
                                'HC':'Corners',
                                'AC':'CornersOpponent',
                                'HY':'YellowCards',
                                'AY':'YellowCardsOpponent',
                                'HR':'RedCards',
                                'AR':'RedCardsOpponent',
                                }, 
                                inplace=True)

    # if FTR = 'H' then 3 points, if FTR = 'A' then 0 points, if FTR = 'D' then 1 point
    results_home['Points'] = results_home['FTR'].apply(lambda x: 3 if x == 'H' else (1 if x == 'D' else 0))

    # create a column after 'Points' called 'Win' and set value to 1 if Points = 3, else 0
    results_home.insert(8, 'Win', results_home['Points'].apply(lambda x: 1 if x == 3 else 0))

    # create a column after 'Win' called 'Draw' and set value to 1 if Points = 1, else 0
    results_home.insert(9, 'Draw', results_home['Points'].apply(lambda x: 1 if x == 1 else 0))

    # create a column after 'Draw' called 'Loss' and set value to 1 if Points = 0, else 0
    results_home.insert(10, 'Loss', results_home['Points'].apply(lambda x: 1 if x == 0 else 0))

    # creare a column called 'GoalDifference' and set value to Goals - GoalsOpponent
    results_home.insert(11, 'GoalDifference', results_home['Goals'] - results_home['GoalsOpponent'])

    # drop columns FTR, HTR
    results_home.drop(['FTR', 'HTR'], axis=1, inplace=True)

    # Process Away Data

    # copy the results dataframe to a new dataframe called results_away
    results_away = results.copy()

    # create a column called Team, after Date. Copy AwayTeam to Team
    results_away.insert(1, 'Team', results_away['AwayTeam'])

    # add columns called Venue with Value 'Away'
    results_away.insert(2, 'Venue', 'Away')

    # change HomeTeam to Opponent
    results_away.rename(columns={'HomeTeam': 'Opponent'}, inplace=True)

    # drop AwayTeam column
    results_away.drop('AwayTeam', axis=1, inplace=True)

    # rename columns FTHG to GoalsFor and FTAG to GoalsAgainst
    results_away.rename(columns={'FTAG': 'Goals', 
                                'FTHG': 'GoalsOpponent', 
                                'HTAG': 'HalfTimeGoals',
                                'HTHG':'HalfTimeGoalsOpponent',
                                'AS':'Shots',
                                'HS':'ShotsOpponent',
                                'AST':'ShotsOnTarget',
                                'HST':'ShotsOnTargetOpponent',
                                'AF':'Fouls',
                                'HF':'FoulsOpponent',
                                'AC':'Corners',
                                'HC':'CornersOpponent',
                                'AY':'YellowCards',
                                'HY':'YellowCardsOpponent',
                                'AR':'RedCards',
                                'HR':'RedCardsOpponent',
                                }, 
                                inplace=True)

    # if FTR = 'A' then 3 points, if FTR = 'H' then 0 points, if FTR = 'D' then 1 point
    results_away['Points'] = results_away['FTR'].apply(lambda x: 3 if x == 'A' else (1 if x == 'D' else 0))

    # create a column after 'Points' called 'Win' and set value to 1 if Points = 3, else 0
    results_away.insert(8, 'Win', results_away['Points'].apply(lambda x: 1 if x == 3 else 0))

    # create a column after 'Win' called 'Draw' and set value to 1 if Points = 1, else 0
    results_away.insert(9, 'Draw', results_away['Points'].apply(lambda x: 1 if x == 1 else 0))

    # create a column after 'Draw' called 'Loss' and set value to 1 if Points = 0, else 0
    results_away.insert(10, 'Loss', results_away['Points'].apply(lambda x: 1 if x == 0 else 0))

    # create a column called 'GoalDifference' and set value to Goals - GoalsOpponent
    results_away.insert(11, 'GoalDifference', results_away['Goals'] - results_away['GoalsOpponent'])

    # drop columns FTR, HTR
    results_away.drop(['FTR', 'HTR'], axis=1, inplace=True)

    # join results_home and results_away dataframes using pd.concat
    results_processed = pd.concat([results_home, results_away], ignore_index=True)

    # if games parameter passed, retain the last x results for each team
    if games:
        results_processed = results_processed.sort_values(by=['Team', 'Date'], ascending=False).groupby('Team').head(games)
        # create a column called 'Table_Games' and store the value of games, place in position 2
        results_processed.insert(1, 'Table_Games', games)
        
    else:
        results_processed.insert(1, 'Table_Games', 'ALL')

    return results_processed

def create_league_table(final_results):
    # create a new dataframe called league_table
    league_table = pd.DataFrame()
    # create a new dataframe called league_table
    league_table = final_results.groupby(['Div','Team']).agg(
        P=pd.NamedAgg(column='Team', aggfunc='count'),
        W=pd.NamedAgg(column='Win', aggfunc='sum'),
        D=pd.NamedAgg(column='Draw', aggfunc='sum'),
        L=pd.NamedAgg(column='Loss', aggfunc='sum'),
        F=pd.NamedAgg(column='Goals', aggfunc='sum'),
        A=pd.NamedAgg(column='GoalsOpponent', aggfunc='sum'),
        GD=pd.NamedAgg(column='GoalDifference', aggfunc='sum'),
        PTS=pd.NamedAgg(column='Points', aggfunc='sum'),
        SH=pd.NamedAgg(column='Shots', aggfunc='sum'),
        SHA=pd.NamedAgg(column='ShotsOpponent', aggfunc='sum'),
        SHT=pd.NamedAgg(column='ShotsOnTarget', aggfunc='sum'),
        SHTA=pd.NamedAgg(column='ShotsOnTargetOpponent', aggfunc='sum'),
        FOULS=pd.NamedAgg(column='Fouls', aggfunc='sum'),
        FOULSA=pd.NamedAgg(column='FoulsOpponent', aggfunc='sum'),
        C=pd.NamedAgg(column='Corners', aggfunc='sum'),
        CA=pd.NamedAgg(column='CornersOpponent', aggfunc='sum'),
        YC=pd.NamedAgg(column='YellowCards', aggfunc='sum'),
        YCA=pd.NamedAgg(column='YellowCardsOpponent', aggfunc='sum'),
        RC=pd.NamedAgg(column='RedCards', aggfunc='sum'),
        RCA=pd.NamedAgg(column='RedCardsOpponent', aggfunc='sum'),
        TABLE_GAMES=pd.NamedAgg(column='Table_Games', aggfunc='max')
    ).reset_index()

    # create a new column called 'W_Perc' and set value to (W/P)*100. Round to 2 decimal places
    league_table['W_Perc'] = round((league_table['W'] / league_table['P']) * 100, 2)

    # create a new column called 'D_Perc' and set value to (D/P)*100. Round to 2 decimal places
    league_table['D_Perc'] = round((league_table['D'] / league_table['P']) * 100, 2)

    # create a new column called 'L_Perc' and set value to (L/P)*100. Round to 2 decimal places
    league_table['L_Perc'] = round((league_table['L'] / league_table['P']) * 100, 2)

    # create a new column called 'G_PG' and set value to GF/P. Round to 2 decimal places
    league_table['G_PG'] = round(league_table['F'] / league_table['P'], 2)

    # create a new column called 'GA_PG' and set value to GA/P. Round to 2 decimal places
    league_table['GA_PG'] = round(league_table['A'] / league_table['P'], 2)

    # create a new column called 'GD_PG' and set value to GD/P. Round to 2 decimal places
    league_table['GD_PG'] = round(league_table['GD'] / league_table['P'], 2)

    # create a new column called 'SH_PG' and set value to SH/P. Round to 2 decimal places
    league_table['SH_PG'] = round(league_table['SH'] / league_table['P'], 2)

    # create a new column called 'SHA_PG' and set value to SHA/P. Round to 2 decimal places
    league_table['SHA_PG'] = round(league_table['SHA'] / league_table['P'], 2)

    # create a new column called 'SHT_PG' and set value to SHT/P. Round to 2 decimal places
    league_table['SHT_PG'] = round(league_table['SHT'] / league_table['P'], 2)

    # create a new column called 'SHTA_PG' and set value to SHTA/P. Round to 2 decimal places
    league_table['SHTA_PG'] = round(league_table['SHTA'] / league_table['P'], 2)

    # create a new column called 'FOULS_PG' and set value to FOULS/P. Round to 2 decimal places
    league_table['FOULS_PG'] = round(league_table['FOULS'] / league_table['P'], 2)

    # create a new column called 'FOULSA_PG' and set value to FOULSA/P. Round to 2 decimal places
    league_table['FOULSA_PG'] = round(league_table['FOULSA'] / league_table['P'], 2)

    # create a new column called 'C_PG' and set value to C/P. Round to 2 decimal places
    league_table['C_PG'] = round(league_table['C'] / league_table['P'], 2)

    # create a new column called 'CA_PG' and set value to CA/P. Round to 2 decimal places
    league_table['CA_PG'] = round(league_table['CA'] / league_table['P'], 2)

    # create a new column called 'YC_PG' and set value to YC/P. Round to 2 decimal places
    league_table['YC_PG'] = round(league_table['YC'] / league_table['P'], 2)

    # create a new column called 'YCA_PG' and set value to YCA/P. Round to 2 decimal places
    league_table['YCA_PG'] = round(league_table['YCA'] / league_table['P'], 2)

    # create a new column called 'RC_PG' and set value to RC/P. Round to 2 decimal places
    league_table['RC_PG'] = round(league_table['RC'] / league_table['P'], 2)

    # create a new column called 'RCA_PG' and set value to RCA/P. Round to 2 decimal places
    league_table['RCA_PG'] = round(league_table['RCA'] / league_table['P'], 2)

    # create a new column called 'PPG' and set value to PTS/P. Round to 2 decimal places
    league_table['PPG'] = round(league_table['PTS'] / league_table['P'], 2)

    # sort league_table by Div, PTS, GD, F, Team, P and reset index
    league_table.sort_values(by=['PTS', 'GD', 'F', 'Team', 'P'], ascending=False, inplace=True)
    league_table.reset_index(drop=True, inplace=True)

    # # create a new column called 'POS' and set value to index + 1. Place it in position 1
    league_table.insert(1, 'POS', league_table.index + 1)

    # create rankng columns

    #create a rank for specific columns
    for col in league_table.columns:
        if col in ['W_Perc','G_PG','GD_PG','SH_PG','SHT_PG','C_PG']:
            league_table[col + '_Rank'] = league_table[col].rank(ascending=False).astype(int)
    #create a reverse rank for specific columns
    for col in league_table.columns:
        if col in ['L_Perc','GA_PG','SA_PG','SHTA_PG','CA_PG']:
            league_table[col + '_Rank'] = league_table[col].rank(ascending=True).astype(int)

    # create a column called 'Rating' that is the average of the ranking columns
    league_table['Rating'] = league_table.filter(regex='_Rank').mean(axis=1).round(2)

    return league_table

def get_fixtures():

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # go to url
        url = "https://thefishy.co.uk/nextweeksfixtures.php"
        # get page into beautifulsoup
        page.goto(url)
        source = page.content()
        soup = BeautifulSoup(source, "html.parser")

    cols = ['League','Match_Date', 'Kick_Off','Home_Team', 'Away_Team']    
    
    fixturelist = []

    match_or_league = ""
    finaldate = ""
    finalleague = ""

    fixtures = soup.findAll('tbody')
    for fixture in fixtures:        
        matches = fixture.findAll('tr')
        for match in matches:
            try:
                if match.find("th"):
                    match_or_league = match.text
                    if re.match(r'\w', match_or_league):
                        finaldate = match_or_league.strip()
                    else:
                        finalleague = match_or_league.strip()
                try:
                    matchcol = match.findAll('td')
                    ko = matchcol[1].text
                    teamsplit = matchcol[0].text.split(" v ")
                    hometeam = teamsplit[0]
                    awayteam = teamsplit[1]
                except:
                    ko = ""
                    hometeam = ""
                    awayteam = ""
                if hometeam != "":
                    fixturelist.append([finalleague,finaldate,ko,hometeam,awayteam])    
            except:
                pass

    final_fixtures = pd.DataFrame(fixturelist, columns=cols)
    
    # trim Home_Team and Away_Team columns
    final_fixtures['Home_Team'] = final_fixtures['Home_Team'].str.strip()
    final_fixtures['Away_Team'] = final_fixtures['Away_Team'].str.strip()

    leagues_to_keep = ['Spanish Segunda',
    'Premier League',
    'Scottish Championship',
    'German Bundesliga',
    'Italian Serie A',
    'Italian Serie B',
    'French Ligue 1',
    'Belgian Pro League',
    'Turkish Super League',
    'Championship',
    'League One',
    'League Two',
    'Scottish Premiership',
    'Scottish League One',
    'Scottish League Two',
    'Spanish La Liga',
    'German 2. Bundesliga',
    'French Ligue 2',
    'Dutch Eredivisie',
    'Greek Super League',
    'Portuguese Primeira',]

    final_fixtures = final_fixtures[final_fixtures['League'].isin(leagues_to_keep)]

    sub_list = ["Mon", "Tues" ,"Tue" ,"Weds" ,"Wed", "Thurs", "Thur", "Thu", "Fri", "Sat", "Sun"]

    final_fixtures['Match_Date'] = final_fixtures['Match_Date'].str.replace('|'.join(sub_list), '').str.strip()
    final_fixtures['Day'] = final_fixtures['Match_Date'].str.extract(r'(\d{1,2})')[0].astype(int)
    final_fixtures['Month'] = final_fixtures['Match_Date'].str.extract(r'(\d{1,2})$')[0].astype(int)

    #get this year and last year
    ty = datetime.datetime.now().year
    ly = ty - 1

    final_fixtures['Year'] = final_fixtures['Month'].apply(lambda x: ty if x <8 else ly)

    final_fixtures['Match_Date'] = final_fixtures.apply(lambda x: datetime.date(x['Year'], x['Month'], x['Day']), axis=1)
    final_fixtures['Match_Date'] = pd.to_datetime(final_fixtures['Match_Date'])

    final_fixtures.drop('Day', axis=1, inplace=True)
    final_fixtures.drop('Month', axis=1, inplace=True)
    final_fixtures.drop('Year', axis=1, inplace=True)        
    return(final_fixtures)


# ****************************** Core Code - n games ****************************** 

def process_leagues(leagues, games_to_compute, results_table, tables_table, engine):
    all_results = pd.DataFrame()
    all_tables = pd.DataFrame()
    
    for league in leagues:
        print(f'Processing {league}')
        results = get_results(league)
        if results.empty:
            continue
        
        final_results = process_results(results, games=games_to_compute)
        if final_results.columns[0] == 'ï»¿Div':
            final_results.rename(columns={'ï»¿Div': 'Div'}, inplace=True)
        
        all_results = pd.concat([all_results, final_results], ignore_index=True)
        table = create_league_table(final_results)
        if not table.empty:
            all_tables = pd.concat([all_tables, table], ignore_index=True)
    
    all_results.to_sql(name=results_table, con=engine, if_exists='replace', index=False)
    all_tables.to_sql(name=tables_table, con=engine, if_exists='replace', index=False)

def main():
    engine = sqlalchemy.create_engine('sqlite:///database.db', pool_pre_ping=True)
    leagues = ['E0','E1','E2','E3','SC0','SC1','SC2','SC3','D1','D2','I1','I2','SP1','SP2','F1','F2','N1','B1','P1','T1','G1']
    
    print('Getting Upcoming Fixtures')
    all_fixtures = get_fixtures()
    all_fixtures.to_sql(name='t_fixtures', con=engine, if_exists='replace', index=False)
    
    process_leagues(leagues, games_to_compute=6, results_table='t_results', tables_table='t_tables', engine=engine)
    process_leagues(leagues, games_to_compute=50, results_table='t_results_season', tables_table='t_tables_season', engine=engine)
    
    engine.dispose()

if __name__ == "__main__":
    main()

# run python app.py to start the app from notebook
# !python app.py
