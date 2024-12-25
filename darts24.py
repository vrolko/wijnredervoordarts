import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Initialize the Selenium WebDriver
service = Service()
driver = webdriver.Chrome(service=service)

url = "https://www.flashscore.com/darts/world/pdc-world-championship/results/"
driver.get(url)

# Parse the page source with BeautifulSoup
soup_main = BeautifulSoup(driver.page_source, 'html.parser')

# Find the div with id 'live-table'
live_table_div = soup_main.find('div', {'id': 'live-table'})

# Extract all <a> hrefs within the div
hrefs = [a['href'] for a in live_table_div.find_all('a', href=True)]

# Skip the first two elements and filter those with /match/
match_hrefs = [href for href in hrefs[2:] if '/match/' in href]

# Extract everything after /match/ to the next /
match_ids = [href.split('/match/')[1].split('/')[0] for href in match_hrefs]

# Load existing CSV file if it exists
csv_file = r'C:\Users\Eelke\PycharmProjects\WijnrederVoorDarts\results.csv'
if os.path.exists(csv_file):
    existing_df = pd.read_csv(
        csv_file)
    existing_ids = existing_df['Match ID'].unique()
else:
    existing_df = pd.DataFrame()
    existing_ids = []

# Process each match ID
for match_id in match_ids:
    if match_id in existing_ids or match_id == 'l4gROckK':
        continue  # Skip already processed match IDs

    # URL of the page to scrape
    url_match = f"https://www.flashscore.com/match/{match_id}/#/match-summary/match-statistics/0"
    driver.get(url_match)

    # Wait for the statistics divs to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='wcl-statistics']"))
    )

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    statistics_divs = soup.find_all('div', {'data-testid': 'wcl-statistics'})

    title = soup.title.string
    title_parts = title.split('|')
    match_result = title_parts[0].strip()
    players = title_parts[1].strip().split('-')
    players = ['Noa-Lynn van Leuven' if player == 'Noa' else player for player in players]

    scores = match_result.split()[1].split('-')
    home_score = int(scores[0])
    away_score = int(scores[1])

    winner, loser = (players[0].strip(), players[1].strip()) if home_score > away_score else (players[1].strip(), players[0].strip())
    players_dict = {'Winner': winner, 'Loser': loser}

    stats = {}
    for statistics_div in statistics_divs:
        home_value = statistics_div.find('div', {'class': 'wcl-homeValue_-iJBW'}).text.strip()
        stat_name = statistics_div.find('div', {'class': 'wcl-category_7qsgP'}).text.strip()
        away_value = statistics_div.find('div', {'class': 'wcl-awayValue_rQvxs'}).text.strip()
        stats[stat_name] = (home_value, away_value)

    legs_won_loser = float(stats['Legs won'][1] if players_dict['Loser'] == players[1].strip() else stats['Legs won'][0])
    legs_won_winner = float(stats['Legs won'][0] if players_dict['Winner'] == players[0].strip() else stats['Legs won'][1])
    most_180s_winner = float(stats['180 thrown'][0] if players_dict['Winner'] == players[0].strip() else stats['180 thrown'][
        1])
    most_180s_loser = float(stats['180 thrown'][1] if players_dict['Loser'] == players[1].strip() else stats['180 thrown'][0])
    highest_checkout_winner = float(stats['Highest checkout'][0] if players_dict['Winner'] == players[0].strip() else \
    stats['Highest checkout'][1])
    highest_checkout_loser = float(stats['Highest checkout'][1] if players_dict['Loser'] == players[1].strip() else \
    stats['Highest checkout'][0])
    average_winner = float(stats['Average (3 darts)'][0] if players_dict['Winner'] == players[0].strip() else \
    stats['Average (3 darts)'][1])
    average_loser = float(stats['Average (3 darts)'][1] if players_dict['Loser'] == players[1].strip() else \
    stats['Average (3 darts)'][0])

    if match_id in ['4dethaEr']:
        dart9_finish = 'Christiaan Kist'
    else:
        dart9_finish = ''

    most_180s_who = 'Both' if most_180s_winner == most_180s_loser else (players_dict['Winner'] if most_180s_winner > most_180s_loser else players_dict['Loser'])
    most_180s_total = int(most_180s_winner) + int(most_180s_loser)
    highest_checkout_who = 'Both' if highest_checkout_winner == highest_checkout_loser else (players_dict['Winner'] if highest_checkout_winner > highest_checkout_loser else players_dict['Loser'])
    average_who = 'Both' if average_winner == average_loser else (players_dict['Winner'] if average_winner > average_loser else players_dict['Loser'])

    points = {
        'Win': 100,
        'Legs Won': 20,
        'Max Checkout': 50,
        'Most 180s': 50,
        '9-Dart Finish': 250,
        'Highest Average': 50
    }

    result_df = pd.DataFrame({
        'Match ID': [match_id] * 12,
        'Stat': ['Game Link', 'Winner', 'Loser', 'Max Checkout', 'Most 180s', 'Total 180s', '9-Dart Finish', 'Highest Average', 'Legs Winner', 'Legs Loser', winner, loser],
        'Who': [url_match, players_dict['Winner'], players_dict['Loser'], highest_checkout_who, most_180s_who, most_180s_total, dart9_finish, average_who, players_dict['Winner'], players_dict['Loser'], most_180s_winner, most_180s_loser],
        'Points': [match_id, points['Win'], '', points['Max Checkout'], points['Most 180s'], '', points['9-Dart Finish'], points['Highest Average'], points['Legs Won'] * int(legs_won_winner), points['Legs Won'] * int(legs_won_loser), '', '']
    })

    # Check for 'Both' in stats and add rows for both players
    # Check for 'Both' in stats and add rows for both players
    if most_180s_who == 'Both':
        result_df = pd.concat([result_df, pd.DataFrame({
            'Match ID': [match_id],
            'Stat': ['Most 180s'],
            'Who': [players_dict['Winner']],
            'Points': [points['Most 180s']]
        })], ignore_index=True)
        result_df = pd.concat([result_df, pd.DataFrame({
            'Match ID': [match_id],
            'Stat': ['Most 180s'],
            'Who': [players_dict['Loser']],
            'Points': [points['Most 180s']]
        })], ignore_index=True)

    if highest_checkout_who == 'Both':
        result_df = pd.concat([result_df, pd.DataFrame({
            'Match ID': [match_id],
            'Stat': ['Max Checkout'],
            'Who': [players_dict['Winner']],
            'Points': [points['Max Checkout']]
        })], ignore_index=True)
        result_df = pd.concat([result_df, pd.DataFrame({
            'Match ID': [match_id],
            'Stat': ['Max Checkout'],
            'Who': [players_dict['Loser']],
            'Points': [points['Max Checkout']]
        })], ignore_index=True)

    if average_who == 'Both':
        result_df = pd.concat([result_df, pd.DataFrame({
            'Match ID': [match_id],
            'Stat': ['Highest Average'],
            'Who': [players_dict['Winner']],
            'Points': [points['Highest Average']]
        })], ignore_index=True)
        result_df = pd.concat([result_df, pd.DataFrame({
            'Match ID': [match_id],
            'Stat': ['Highest Average'],
            'Who': [players_dict['Loser']],
            'Points': [points['Highest Average']]
        })], ignore_index=True)

    # Append the new result_df to the existing DataFrame
    existing_df = pd.concat([existing_df, result_df], ignore_index=True)

# Save the updated DataFrame to the CSV file
existing_df.to_csv(csv_file, index=False)

existing_df = existing_df.drop(columns=['Match ID'])
existing_df.to_clipboard(index=False, header=False)
# Close the WebDriver
driver.quit()