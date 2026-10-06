import streamlit as st
import pandas as pd
import plotly.express as px
import re


st.set_page_config(page_title='Pick your Movie', layout='wide')
@st.cache_data
def load_data():
    df = pd.read_excel('project1 popularity.xlsx')
    df['genres'] = df['genres'].fillna('').astype(str)
    df['release year'] = pd.to_datetime(df['release_date'], format='%d-%m-%y', errors='coerce').dt.year
    return df

df = load_data()

min_year = int(df['release year'].min())
max_year = int(df['release year'].max())

min_popularity = float(df['popularity'].min())
max_popularity = float(df['popularity'].max())
st.title('Pick your Movie')

all_genres = sorted({
  g.strip()
  for genres in df['genres']
  for g in genres.replace('[','').replace(']','').replace("'","").split(',')
  if g.strip()
})

st.sidebar.header('filters')
selected_genres = st.sidebar.multiselect('select genre(s)', all_genres, default = all_genres[:3])

min_rating =  float(df['vote_average'].min())
max_rating = float(df['vote_average'].max())
min_vote = st.sidebar.slider('minimum rating', min_rating, max_rating, min_rating)

popularity = st.sidebar.slider(
    'popularity',
    min_value = min_popularity,
    max_value = max_popularity,
    value = min_popularity
)
year_range = st.sidebar.slider(
    'year range',
    min_value = min_year,
    max_value = max_year,
    value = (min_year, max_year)
)


def genre_match(cell: str, genres: list[str]) -> bool:
    cell = cell.lower()
    return any(re.search(rf'\b{re.escape(g.lower())}\b',cell) for g in genres)

filtered = df.copy()
if selected_genres:
    filtered = filtered[filtered['genres'].apply(lambda x: genre_match(x, selected_genres))]

filtered = filtered[filtered['vote_average'] >= min_vote]
filtered = filtered[
    (filtered['release year'] >= year_range[0]) &
    (filtered['release year'] <= year_range[1])
]

col1, col2, col3 = st.columns(3)
col1.metric("Movies",len(filtered))
col2.metric("Avg Rating", round(filtered['vote_average'].mean(),2)if len(filtered) else 0)
col3.metric("Top Rating", round(filtered['vote_average'].max(),2)if len(filtered) else 0)

st.divider()

c1,c2 = st.columns(2)

with c1:
    st.subheader('Rating distribution')
    if len(filtered):
      st.plotly_chart(px.histogram(filtered, x='vote_average', nbins=20),
                      use_container_width=True)
    else:
        st.info("No Movies match")

with c2:
    st.subheader("Top 10 rated movies")
    if len(filtered):
      top10 = filtered.nlargest(10, 'vote_average')[['title', 'vote_average']]
      fig = px.bar(top10, x='vote_average', y='title', orientation='h')
      fig.update_layout(yaxis={'categoryorder': 'total ascending'})
      st.plotly_chart(fig, use_container_width=True)

st.divider()
if len(filtered):
  fig = px.scatter(
      filtered,
      x='budget',
      y='revenue',
      color='genres',
      hover_data=['title'],
      title = 'budget vs revenue'
  )
  st.plotly_chart(fig, use_container_width=True)




st.subheader("Filtered data")
st.dataframe(filtered[['title', 'genres', 'vote_average','release year']], use_container_width=True)

st.subheader("Highest rated per genre")
if selected_genres:
    for genre in selected_genres:
        sub = filtered[filtered['genres'].apply(lambda x: genre_match(x, [genre]))]
        if not sub.empty:
            idx = sub['vote_average'].idxmax()
            st.write(f"**{genre}**: {sub.loc[idx, 'title']} — {sub.loc[idx, 'vote_average']} ⭐ , ({sub.loc[idx, 'release year']})")