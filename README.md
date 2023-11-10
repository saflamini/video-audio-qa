## Q&A Over YT Videos and Podcasts

Use speech to text models and LLMs to process Youtube videos and podcasts 10x as fast.

This is a personal tool I created which makes it easy to find interesting moments within longer podcasts and youtube videos. Video & audio content is often harder to parse/skim through than written content, but running tool makes this easier to manage.

This app is also a great demonstration of [AssemblyAI's](https://www.assemblyai.com/) product suite which includes automatic speech recognition, automatic chapter generation, and [LeMUR](https://www.assemblyai.com/models/lemur/) - a framework for pairing transcripts with LLMs.

### Running this project

I recommend that you start by running this project locally. If you want to deploy it, you can do so using the Streamlit community cloud or your method of choice.

This is a streamlit app, with all logic in `qa.py` 

Follow these steps to run the app:

#### Sign Up For Supabase

This app uses [Supabase](https://supabase.com) for persistent transcript storage.

Create a new project, then add the Supabase URL and Supabase Key as local environment variables like this:
- `export SUPABASE_URL=YOUR_SUPABASE_URL`
- `export SUPABASE_KEY=YOUR_SUPABASE_KEY`

You'll need to create a new table in supabase called `transcripts` and add 2 text columns: `content_name` and `transcript_id`

You can rename the table and the columns if you'd like, but if you do so be sure to make the modifications necessary in `qa.py``

#### Get an AssemblyAI API Key

Head to assemblyai.com and sign up for an API Key, then add this to your local env variables:
- `export ASSEMBLYAI_API_KEY=YOUR_AAI_KEY`


#### Install Deps and Run

Once you have Supabase and AssemblyAI ready to go, you can install deps and run the app.

`pip install -r requirements.txt`

`streamlit run qa.py`

