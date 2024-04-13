from bs4 import BeautifulSoup
import lxml
import requests, pandas as pd
import re
from requests.exceptions import RequestException
#from pandas.io.json import JsonWriteException

base_url = 'https://www.imdb.com'
url = 'https://www.imdb.com/list/ls055592025/'
response = requests.get(url) #  gets the content of the website
content = response.text

try:
    response = requests.get(url)
    response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
except RequestException as e:
    print(f"An error occurred while fetching the webpage: {e}")
else:
    content = response.text
    soup = BeautifulSoup(content, 'lxml')

movie_titles = soup.find_all('div', class_='lister-item-content')

titles = []
rankings = []
released_years = []
certificates = []
lengths = []
genres = []
metascores = []
directors = []
stars = []
votes = []
gross = []
links = []
for title in movie_titles:
    rankings.append(title.find('span', class_='lister-item-index unbold text-primary').get_text(strip=True))
    titles.append(title.find('a').get_text(strip=True))
    year = title.find('span', class_='lister-item-year text-muted unbold')
    released_years.append(year.get_text(strip=True) if year else 'N/A')
    certificate = title.find('span', class_='certificate')
    certificates.append(certificate.get_text(strip=True) if certificate else 'N/A')
    length = title.find('span', class_='runtime')
    lengths.append(length.get_text(strip=True) if length else 'N/A')
    genre = title.find('span', class_='genre')
    genres.append(genre.get_text(strip=True).strip() if genre else 'N/A')
    
    metascore = title.select_one("div.inline-block.ratings-metascore span")
    metascores.append(metascore.get_text(strip=True) if metascore else 'N/A')

    links.append(base_url + title.find('a').get('href'))

    # Extracting director(s)
    director = title.find('a', href=re.compile(r'/name/nm'))
    directors.append(director.get_text(strip=True) if director else 'N/A')

    # Extracting stars
    stars_list = title.find_all('a', href=re.compile(r'/name/nm'))
    # The first 'a' tag with '/name/nm' is usually the director, so we ignore it in stars
    stars_names = [star.get_text(strip=True) for star in stars_list[1:]] if stars_list else []
    stars.append(", ".join(stars_names))

    # Extracting votes and gross
    nv_tags = title.find_all('span', attrs={'name': 'nv'})
    votes.append(nv_tags[0].get_text(strip=True) if nv_tags and len(nv_tags) > 0 else 'N/A')
    gross.append(nv_tags[1]['data-value'] if nv_tags and len(nv_tags) > 1 else 'N/A')


actors_ratings = []
direction_ratings = []
screenplay_ratings = []
oscars = []
oscar_nominations = []
bafta_awards = []
bafta_nominations = []
goldens_globes = []
goldens_globe_nominations = []


movie_data = soup.find_all('div', class_='list-description')
for data in movie_data:

    data_text = data.findChild('p').text
    # Regular expression to match text after ':'
    pattern = re.compile(r':\s*([^\n:]+)')


    # Find all matches
    values = pattern.findall(data_text)

    if len(values) > 2:
        # Manually assigning each item to the corresponding list
        actors_ratings.append(values[0].split()[0])
        direction_ratings.append(values[1].split()[0])
        screenplay_ratings.append(values[2].split()[0])
        oscars.append(values[3])
        oscar_nominations.append(values[4])
        bafta_awards.append(values[5])
        bafta_nominations.append(values[6])
        goldens_globes.append(values[7])
        goldens_globe_nominations.append(values[8])

# Create DataFrame
movies_df = pd.DataFrame({
    # Print the lists to verify
    "ranking": rankings,
    "title": titles,
    "genre": genres,
    "certificate": certificates,
    "release_year": released_years,
    "runtime":lengths,
    "metascore_rating": metascores,
    "directors": directors,  # Add the new list for directors
    "stars": stars,          # Add the new list for stars
    "votes": votes,          # Add the new list for votes
    "gross_revenue": gross,          # Add the new list for gross revenue
    "actors_atings": actors_ratings,
    "direction_atings": direction_ratings,
    "screenplay_ratings": screenplay_ratings,
    "oscars": oscars,
    "oscar_nominations": oscar_nominations,
    "bafta_awards": bafta_awards,
    "bafta_nominations": bafta_nominations,
    "golden_globes": goldens_globes,
    "golden_globe_nominations": goldens_globe_nominations,
    "link": links
})

# Sort the DataFrame by 'upvote'
movies_df = movies_df.sort_values(by='ranking', ascending=True)

try:
    movies_df.to_json('movies.json', orient='records', lines=True)
    movies_df.to_csv('movies.csv', index=False)
    print("The movies.json and movies.csv files have been created")
except Exception as e:  # Catch any exception that might occur during file operations
    print(f"An error occurred while writing to files: {e}")
