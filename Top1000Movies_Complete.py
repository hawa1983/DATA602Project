from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import time
import numpy as np  # Make sure to add this import statement

def extract_movie_data(page_content):
    # Parsing the content of the page to a BeautifulSoup object
    soup = BeautifulSoup(page_content, 'lxml')

    movie_data = []
    movie_titles = soup.find_all('div', class_='lister-item-content')
    for title in movie_titles:
        data = {
            'Ranking': title.find('span', class_='lister-item-index unbold text-primary').get_text(strip=True),
            'Title': title.find('a').get_text(strip=True),
            'Release Year': title.find('span', class_='lister-item-year text-muted unbold').get_text(strip=True) if title.find('span', class_='lister-item-year text-muted unbold') else 'N/A',
            'Certificate': title.find('span', class_='certificate').get_text(strip=True) if title.find('span', class_='certificate') else 'N/A',
            'Runtime': title.find('span', class_='runtime').get_text(strip=True) if title.find('span', class_='runtime') else 'N/A',
            'Genre': title.find('span', class_='genre').get_text(strip=True).strip() if title.find('span', class_='genre') else 'N/A',
            'Metascore': title.select_one("div.inline-block.ratings-metascore span").get_text(strip=True) if title.select_one("div.inline-block.ratings-metascore span") else 'N/A',
            'Director': ", ".join([a.get_text(strip=True) for a in title.select('p.text-muted.text-small a[href*="/name/nm"]')]),
            'Stars': ", ".join([a.get_text(strip=True) for a in title.select('p.text-muted.text-small a[href*="/name/nm"]:not([href*="/name/nm0000116"])')]),
            'Votes': title.find('span', attrs={'name': 'nv'}).get_text(strip=True) if title.find('span', attrs={'name': 'nv'}) else 'N/A',
            'Gross Revenue': title.find_all('span', attrs={'name': 'nv'})[1]['data-value'] if len(title.find_all('span', attrs={'name': 'nv'})) > 1 else 'N/A',
            'Link': "https://www.imdb.com" + title.find('a').get('href')
        }
        print(data)
        movie_data.append(data)
    return movie_data

def get_next_page(soup):
    next_button = soup.find('a', class_='flat-button lister-page-next next-page')
    return next_button.get('href') if next_button else None

# The headers to mimic a browser visit
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
}

def scrape_imdb_list(base_url, current_page):
    all_movies = []
    while current_page:
        try:
            response = requests.get(base_url + current_page, headers=headers)
            response.raise_for_status()
            all_movies.extend(extract_movie_data(response.content))
            soup = BeautifulSoup(response.content, 'lxml')
            current_page = get_next_page(soup)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            break

    return pd.DataFrame(all_movies)

# Start scraping
base_url = "https://www.imdb.com"
current_page = "/list/ls098063263/"
movies_df = scrape_imdb_list(base_url, current_page)

# Save to CSV and JSON
movies_df.to_csv('movies.csv', index=False)
movies_df.to_json('movies.json', orient='records', lines=True)

# ... [Include the functions for scraping awards and financials] ...

# ... [Combine the data from awards and financials with movies_df as before] ...
# Function to scrape wins and nominations
# def scrape_awards(link):
#     try:
#         response = requests.get(link, headers=headers)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')
#         awards_info = soup.find('span', class_='ipc-metadata-list-item__list-content-item')
#         if awards_info:
#             awards_text = awards_info.get_text(strip=True)
#             matches = re.search(r'(\d+) wins? & (\d+) nominations?', awards_text)
#             if matches:
#                 return int(matches.group(1)), int(matches.group(2))
#             else:
#                 return 'N/A', 'N/A'
#         else:
#             return 'N/A', 'N/A'
#     except requests.exceptions.RequestException as e:
#         print(f"Request exception occurred: {e}")
#         return 'N/A', 'N/A'

# Function to scrape financial details like budget and gross
def scrape_financials(soup):
    financial_data = {
        'Budget': 'N/A',
        'Opening Weekend USA': 'N/A',
        'Gross USA': 'N/A',
        'Cumulative Worldwide Gross': 'N/A'
    }

    list_items = soup.find_all('li', class_='ipc-metadata-list__item')
    for item in list_items:
        label_elem = item.find('span', class_='ipc-metadata-list-item__label')
        content_elem = item.find('span', class_='ipc-metadata-list-item__list-content-item')
        if label_elem and content_elem:
            label = label_elem.text.strip()
            content = content_elem.text.strip()
            # Clean up the content by removing non-numeric characters except for the period and comma
            cleaned_content = re.sub(r'[^\d.,]', '', content)

            # Match the label with the corresponding key in the financial_data dictionary
            if re.search(r'Budget', label, re.IGNORECASE):
                financial_data['Budget'] = cleaned_content
                print(f"Debug: Budget - {financial_data['Budget']}")  # Debugging statement
            elif re.search(r'Opening weekend', label, re.IGNORECASE):
                financial_data['Opening Weekend USA'] = cleaned_content
                print(f"Debug: Opening Weekend USA - {financial_data['Opening Weekend USA']}")  # Debugging statement
            elif re.search(r'Gross USA|Gross US & Canada', label, re.IGNORECASE):
                financial_data['Gross USA'] = cleaned_content
                print(f"Debug: Gross USA - {financial_data['Gross USA']}")  # Debugging statement
            elif re.search(r'Cumulative Worldwide Gross|Gross worldwide', label, re.IGNORECASE):
                financial_data['Cumulative Worldwide Gross'] = cleaned_content
                print(f"Debug: Cumulative Worldwide Gross - {financial_data['Cumulative Worldwide Gross']}")  # Debugging statement
                
    return financial_data


# # Function to scrape wins and nominations
def scrape_awards(soup):  # Expect BeautifulSoup object as argument
    try:
        awards_info = soup.find('span', class_='ipc-metadata-list-item__list-content-item')
        if awards_info:
            awards_text = awards_info.get_text(strip=True)
            print(f"Debug: Award Text - {awards_text}")  # Debugging print statement
            matches = re.search(r'(\d+) wins? & (\d+) nominations?', awards_text)
            if matches:
                awards_dict = {
                    'Wins': int(matches.group(1)),
                    'Nominations': int(matches.group(2))
                }
                print(awards_dict)  # Debugging print statement before the return
                return awards_dict
            else:
                awards_dict = {
                    'Wins': 'N/A',
                    'Nominations': 'N/A'
                }
                print(awards_dict)  # Debugging print statement before the return
                return {'Wins': 'N/A', 'Nominations': 'N/A'}
        else:
            awards_dict = {
                'Wins': 'N/A',
                'Nominations': 'N/A'
            }
            print(awards_dict)  # Debugging print statement before the return
            return {'Wins': 'N/A', 'Nominations': 'N/A'}
    except Exception as e:
        print(f"Error scraping awards: {e}")
        return {'Wins': 'N/A', 'Nominations': 'N/A'}


def scrape_additional_details(soup):
    additional_data = {
        'Countries of Origin': [],
        'Languages': [],
        'Production Companies': []
    }

    # Countries of Origin
    countries = soup.select('li.ipc-metadata-list__item a.ipc-metadata-list-item__list-content-item--link[href*="country_of_origin"]')
    additional_data['Countries of Origin'] = [country.get_text(strip=True) for country in countries]

    # Languages
    languages = soup.select('li.ipc-metadata-list__item a.ipc-metadata-list-item__list-content-item--link[href*="primary_language"]')
    additional_data['Languages'] = [language.get_text(strip=True) for language in languages]

    # Production Companies
    companies = soup.select('li.ipc-metadata-list__item a.ipc-metadata-list-item__list-content-item--link[href*="/company/"]')
    additional_data['Production Companies'] = [company.get_text(strip=True) for company in companies]

    # Printing debug statements for each section
    print(f"Debug: Countries of Origin - {additional_data['Countries of Origin']}")
    print(f"Debug: Languages - {additional_data['Languages']}")
    print(f"Debug: Production Companies - {additional_data['Production Companies']}")

    return additional_data

def scrape_release_date(soup):
    # Find the 'a' tag with text 'Release date', then navigate to its parent and sibling to find the date
    release_date_label = soup.find('a', string="Release date")
    if release_date_label:
        release_date_container = release_date_label.find_next_sibling('div')
        if release_date_container:
            release_date = release_date_container.get_text(strip=True)
            print(f"Debug: Release Date - {release_date}")
            return release_date
    return 'N/A'

# Iterate over the DataFrame to scrape awards and financial data
awards_data = []
financial_data = []
release_date_data = []

# Main loop to iterate over movie links and collect all data
for index, row in movies_df.iterrows():
    link = row['Link']
    try:
        response = requests.get(link, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Scrape release date, awards, financial data, and additional details
        release_date = scrape_release_date(soup)
        movies_df.at[index, 'Release Date'] = release_date
        
        awards_data = scrape_awards(soup)
        financial_data = scrape_financials(soup)
        additional_details = scrape_additional_details(soup)
                
        # Update the movies_df DataFrame with the scraped data
        movies_df.at[index, 'Wins'] = awards_data['Wins'] if awards_data['Wins'] != 'N/A' else np.nan
        movies_df.at[index, 'Nominations'] = awards_data['Nominations'] if awards_data['Nominations'] != 'N/A' else np.nan
        movies_df.at[index, 'Budget'] = financial_data['Budget']
        movies_df.at[index, 'Opening Weekend USA'] = financial_data['Opening Weekend USA']
        movies_df.at[index, 'Gross USA'] = financial_data['Gross USA']
        movies_df.at[index, 'Cumulative Worldwide Gross'] = financial_data['Cumulative Worldwide Gross']
        movies_df.at[index, 'Countries of Origin'] = ", ".join(additional_details['Countries of Origin'])  # Convert list to comma-separated string
        movies_df.at[index, 'Languages'] = ", ".join(additional_details['Languages'])  # Convert list to comma-separated string
        movies_df.at[index, 'Production Companies'] = ", ".join(additional_details['Production Companies'])  # Convert list to comma-separated string
        
        # Be polite and sleep to avoid overloading the server
        time.sleep(1)
    
    except requests.exceptions.RequestException as e:
        print(f"Request exception for {link}: {e}")

# Get a list of columns in the DataFrame
columns = list(movies_df.columns)

# Remove 'Link' from the list
columns.remove('Link')

# Add 'Link' at the end of the list
columns.append('Link')

# Reindex the DataFrame with the new column order
movies_df = movies_df.reindex(columns=columns)

# Now you can save the DataFrame to disk
# Save the final combined DataFrame to file
movies_df.to_csv('complete_movies_data.csv', index=False)
movies_df.to_json('complete_movies_data.json', orient='records', lines=True)

print("Data extraction complete. Files saved.")
