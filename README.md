# Setup
1. `source env/bin/activate`
2. `pip install -r requirements.txt`
3. create a `.env` and populate it

## `.env`
```
# fetched from https://developer.twitter.com/en/apps (callback was from docs)
oauth_callback=oob
oauth_consumer_key=xxx
oauth_consumer_secret=xxx

# fetched from fetching the auth token once
oauth_token=xxx
oauth_token_secret=xxx

# user information
auth_user_screen_name=xxx
```

### fetching user context auth token
1. in `main.py` call the `user_context_auth()` manually, and follow the CLI instructions
2. paste the oauth values in the `.env`

# Cleanup
`deactivate`

# Start script
`python main.py`

# Adding more tweets
1. open `tweets.json` file
2. you _must_ add a picture to the `resources/pictures/` folder
3. add a new tweet somewhere in the list in the format of:
```
{
	"img": <name of image>,
	"text": "tweet text"
}
```
4. save the file, and wait for the tweet service to pick it up

# Debugging tips
- after starting, check the output in `output.log`

# Notes
- `env/` was created via `python3 -m venv env`
- `requirements.txt` was created via `pip freeze`