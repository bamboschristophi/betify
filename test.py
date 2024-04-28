def get_fixtures():
    import re
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup
    import pandas as pd
    import datetime

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

    final_fixtures = pd.DataFrame(fixturelist, columns=cols)

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
    final_fixtures['Day'] = final_fixtures['Match_Date'].str[:2].astype(int)
    final_fixtures['Month'] = final_fixtures['Match_Date'].str[3:].astype(int)

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

fixt = get_fixtures()
print(fixt)

